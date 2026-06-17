# B1 Deep-parse Helper — Feature Design

**Date:** 2026-06-17
**Status:** Design (Workflow 2, step 1)
**Epic:** `vgmdb-bzf.1` (B1 Deep-parse helper) — parent `vgmdb-bzf` (Beta)
**Major scope:** `vgmdb_client`
**Vision:** `docs/superpowers/2026-06-14_vgmdb_client.md`
**Depends on:** M1 Models, M3 Parsers, M4 Client (all merged)

## Purpose

Opt-in enrichment of vgmdb freeform fields — primarily **per-track credits** that live in the raw
`notes` block which M3 deliberately leaves unstructured (e.g. album 271 "10. Glitter Girl…
Performed by X / Words by Y"; album 33000 "Arrangement by Syrufit (2,3,5,7,10)"). Given a parsed
`Album` and a pluggable backend, the helper returns a structured **overlay** without changing the
M1 models. First backend: an OpenAI-compatible HTTP endpoint configured by `LLM_URL`.

## Scope

**In scope**
- An `AlbumEnrichment` overlay (per-track credits), separate from the M1 models.
- A pluggable `EnrichmentBackend` Protocol; first impl `OpenAICompatibleBackend` (LLM via `LLM_URL`).
- `enrich_album(album, backend=None)` — graceful empty result when no backend.
- Deterministic tests (stub backend; respx-mocked HTTP backend). No live LLM calls.

**Out of scope (tracked elsewhere)**
- Album-level detailed-role enrichment beyond per-track credits (additive later).
- The embedded lightweight-ML backend (future; the Protocol leaves room).
- `Client` integration sugar (deferred; MVP is the standalone helper).
- The parsing-quality harness → B2 (`vgmdb-bzf.2`); more entities → B3.
- No M1 model/schema change.

## Decisions

**D1 — Separate enrichment overlay (no schema change).** `enrich_album(album) -> AlbumEnrichment`,
a distinct object layered on the `Album`. M1 models + M3 parser stay the deterministic ground truth;
enrichment is an explicit, separable layer with clear provenance (parsed vs LLM-inferred), nothing
re-touches the M5 goldens, and it is ideal input for B2's parser-vs-LLM comparison. *Alternative:*
add `Track.credits` to M1 — rejected (schema churn, murky provenance, mixes deterministic + inferred).

**D2 — Overlay shape: per-track credits keyed by track number.** `AlbumEnrichment{ album_id: int,
track_credits: dict[int, list[Credit]] }` with an `is_empty` property. Reuses the existing `Credit`
and `ArtistRef`. Track number is the natural key (notes reference "10. …"). Frozen / `extra="forbid"`
like the M1 models.

**D3 — Pluggable seam at the enrichment level.** `EnrichmentBackend` is a `Protocol` with
`enrich(album: Album, raw_text: str) -> AlbumEnrichment`. The LLM backend owns its prompt + HTTP +
parse internally; a future embedded-ML backend implements the same Protocol without chat-completion
assumptions. *Alternative:* a low-level `complete(messages) -> str` seam — rejected; an ML backend
shares nothing below the enrichment level.

**D4 — `OpenAICompatibleBackend` over httpx.** `OpenAICompatibleBackend(url, model, api_key=None,
timeout=...)` POSTs an OpenAI-compatible `/chat/completions` request via **httpx (already a runtime
dependency)** and parses the JSON content into `AlbumEnrichment`. A `backend_from_env()` helper reads
`LLM_URL` (+ optional `LLM_MODEL`/`LLM_API_KEY`) and returns the backend, or `None` when `LLM_URL`
is unset. **No new runtime dependency and no `vgmdb-client[llm]` extra is added** — the extra is
reserved for the future embedded-ML backend (YAGNI).

**D5 — Deterministic role normalization.** The LLM is prompted to extract `{track_number, role_raw,
artist names}`; we apply the existing `normalize_role(role_raw)` ourselves rather than trusting the
LLM's normalized role, so enrichment role normalization stays identical to M3.

**D6 — Graceful degradation.** `enrich_album(album, backend=None)` → an **empty `AlbumEnrichment`**
(non-fatal; the M3 `Album` is fully usable; callers check `enrichment.is_empty`). A *configured*
backend that fails (HTTP error, non-JSON, schema-invalid response) raises a typed `EnrichmentError`
(the caller opted in; failures are honest).

## Data flow

```
enrich_album(album, backend):
  backend is None ─▶ AlbumEnrichment(album_id, track_credits={})   # graceful empty
  backend set     ─▶ backend.enrich(album, album.notes or "")
        OpenAICompatibleBackend.enrich:
          build prompt(tracklist + raw notes) ─▶ POST LLM_URL /chat/completions (httpx)
          ─▶ parse JSON content ─▶ normalize_role(role_raw) per credit
          ─▶ AlbumEnrichment.model_validate   (EnrichmentError on HTTP/JSON/schema failure)
```

## Structure

- `src/vgmdb_client/enrich/models.py` — `AlbumEnrichment` (+ `is_empty`).
- `src/vgmdb_client/enrich/backend.py` — `EnrichmentBackend` Protocol.
- `src/vgmdb_client/enrich/llm.py` — `OpenAICompatibleBackend`, `backend_from_env`.
- `src/vgmdb_client/enrich/errors.py` — `EnrichmentError(VgmdbClientError)`.
- `src/vgmdb_client/enrich/__init__.py` — `enrich_album`, `AlbumEnrichment`, `EnrichmentBackend`,
  `OpenAICompatibleBackend`, `backend_from_env`, `EnrichmentError`.

## Testing

- `enrich_album(album, None)` → empty enrichment (`is_empty`).
- A stub backend returning a canned `AlbumEnrichment` → `enrich_album` returns it.
- `OpenAICompatibleBackend` via **respx**: mock `LLM_URL` `/chat/completions` returning canned JSON;
  assert it parses into `AlbumEnrichment` with `normalize_role` applied (use a fixture album whose
  notes carry per-track credits, e.g. 271).
- Invalid/non-JSON response and HTTP error → `EnrichmentError`.
- Backend Protocol conformance; `AlbumEnrichment` model conventions (frozen / extra-forbid).
- `ruff`, `mypy`, full suite green. No live LLM calls.

## Risks / Trade-offs

- **LLM non-determinism** → the pluggable backend is mocked in tests; only the parse/validate/normalize
  pipeline is asserted, not LLM quality (quality measurement is B2).
- **Track-number keying** assumes tracks are numbered; tracks without a number simply can't be enriched
  by this overlay (acceptable for MVP; album/disc-scoped enrichment is a later concern).
- **Prompt/endpoint variability** → `EnrichmentError` on malformed responses keeps failures explicit;
  the overlay is always optional, so consumers degrade to M3 data.

## Acceptance criteria (from the epic)

- Given a parsed album + raw freeform text, the helper returns enriched structured fields via an
  OpenAI-compatible endpoint configured by `LLM_URL`; degrades gracefully when unset; backend is
  pluggable.

## Open questions / deferrals

- `Client` integration sugar (`enrichment_backend=`, `get_album(..., enrich=True)`) — deferred.
- Album-level detailed-role enrichment and the embedded-ML backend — deferred (Protocol leaves room).
