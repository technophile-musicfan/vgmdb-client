## Context

M3 leaves the album `notes` block as raw text; per-track credits live there. B1 adds an opt-in
helper that structures that text into an `AlbumEnrichment` overlay, leaving the M1 models / M3 parser
as the deterministic ground truth. Source of truth:
`docs/superpowers/vgmdb_client/2026-06-17_deep_parse_design.md`. `pydantic` and `httpx` are already
dependencies.

## Goals / Non-Goals

**Goals:**
- An `AlbumEnrichment` overlay (per-track credits) separate from the M1 models.
- A pluggable `EnrichmentBackend` Protocol; first impl over an OpenAI-compatible HTTP endpoint.
- `enrich_album(album, backend=None)` with graceful empty result when unconfigured.
- Deterministic, mockable tests (no live LLM calls).

**Non-Goals:**
- Album-level detailed-role enrichment; the embedded-ML backend; `Client` sugar.
- The quality harness (B2); more entities (B3). No M1 schema change.

## Decisions

**D1 — Separate overlay, no schema change.** `enrich_album(album) -> AlbumEnrichment`; M1 models +
M3 stay deterministic ground truth; enrichment is a separable, clearly-provenanced layer (ideal B2
input). *Alternative:* add `Track.credits` — rejected (schema churn, murky provenance).

**D2 — Overlay shape.** `AlbumEnrichment{ album_id: int, track_credits: dict[int, list[Credit]] }`
with `is_empty`; reuses `Credit`/`ArtistRef`; frozen / `extra="forbid"`. Keyed by track number (notes
reference "10. …").

**D3 — Pluggable seam at the enrichment level.** `EnrichmentBackend` Protocol:
`enrich(album, raw_text) -> AlbumEnrichment`. The LLM backend owns prompt + HTTP + parse; a future ML
backend implements the same Protocol. *Alternative:* low-level `complete(messages)` — rejected (an ML
backend shares nothing below the enrichment level).

**D4 — `OpenAICompatibleBackend` over httpx.** POSTs `/chat/completions` to `LLM_URL`
(`OpenAICompatibleBackend(url, model, api_key=None, timeout=...)`); `backend_from_env()` reads
`LLM_URL`/`LLM_MODEL`/`LLM_API_KEY` and returns the backend or `None` when `LLM_URL` is unset. No new
runtime dependency; no `[llm]` extra yet (reserved for the future ML backend).

**D5 — Deterministic role normalization.** The LLM extracts `{track_number, role_raw, artist names}`;
we apply `normalize_role(role_raw)` ourselves so enrichment roles match M3 exactly.

**D6 — Graceful degradation.** No backend → empty `AlbumEnrichment` (non-fatal; M3 `Album` fully
usable; `enrichment.is_empty`). A configured backend that fails (HTTP/non-JSON/schema-invalid) raises
`EnrichmentError`.

## Data flow

```
enrich_album(album, backend):
  backend is None ─▶ AlbumEnrichment(album_id, {})                  # graceful empty
  backend set     ─▶ backend.enrich(album, album.notes or "")
      OpenAICompatibleBackend.enrich:
        prompt(tracklist + raw notes) ─▶ POST LLM_URL /chat/completions (httpx)
        ─▶ parse JSON ─▶ normalize_role(role_raw) per credit ─▶ AlbumEnrichment.model_validate
        (EnrichmentError on HTTP / non-JSON / schema failure)
```

## Risks / Trade-offs

- **LLM non-determinism** → backend is mocked in tests; only parse/validate/normalize is asserted
  (quality is B2's concern).
- **Track-number keying** assumes numbered tracks; unnumbered tracks aren't enriched (acceptable MVP).
- **Endpoint/response variability** → `EnrichmentError` keeps failures explicit; the overlay is always
  optional so consumers degrade to M3 data.

## Migration Plan

Additive — a new `enrich` package only. No changes to models, parsers, transport, or client.

## Open Questions

- `Client` integration sugar and album-level enrichment — deferred; the Protocol leaves room.
