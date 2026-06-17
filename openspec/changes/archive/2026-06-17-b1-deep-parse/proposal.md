## Why

M3 parses the structural album fields but deliberately leaves the freeform `notes` block as raw
text — yet that block is where per-track credits live (e.g. album 271 "10. Glitter Girl… Performed
by X / Words by Y"; album 33000 "Arrangement by Syrufit (2,3,5,7,10)"). B1 adds an **opt-in**
helper that turns that freeform text into a structured **overlay** without touching the M1 models,
so consumers who want per-track credits can get them while the deterministic parse stays clean.

## What Changes

- Add an **`enrich` package** (`src/vgmdb_client/enrich/`):
  - `AlbumEnrichment` overlay model — `track_credits: dict[int, list[Credit]]` (per-track `Credit`s
    keyed by track number) + an `is_empty` property. Reuses `Credit`/`ArtistRef`; no M1 change.
  - `EnrichmentBackend` **Protocol**: `enrich(album, raw_text) -> AlbumEnrichment` (the pluggable
    seam; a future embedded-ML backend implements the same Protocol).
  - `OpenAICompatibleBackend` over **httpx** — POSTs an OpenAI-compatible `/chat/completions` to
    `LLM_URL`, parses the JSON into `AlbumEnrichment`; `backend_from_env()` returns it or `None`
    when `LLM_URL` is unset.
  - `enrich_album(album, backend=None) -> AlbumEnrichment` — graceful **empty** enrichment when no
    backend; `EnrichmentError` when a configured backend fails (HTTP/JSON/schema).
  - Deterministic role normalization: `normalize_role(role_raw)` is applied by us, not the LLM.

Out of scope (tracked separately): album-level detailed-role enrichment and the embedded-ML backend
(the Protocol leaves room); `Client` integration sugar (deferred); the parsing-quality harness → B2
(`vgmdb-bzf.2`); more entities → B3 (`vgmdb-bzf.3`). No M1 model/schema change. No new runtime
dependency and no `vgmdb-client[llm]` extra yet (httpx-based).

## Capabilities

### New Capabilities
- `enrich`: An opt-in deep-parse overlay — `AlbumEnrichment` (per-track credits), a pluggable
  `EnrichmentBackend` Protocol, an `OpenAICompatibleBackend` (LLM via `LLM_URL`), and
  `enrich_album(album, backend=None)` that degrades to an empty overlay when unconfigured. Keeps the
  M1 models as deterministic ground truth.

### Modified Capabilities
<!-- None — `models`, `parsers`, and `client` are consumed unchanged. -->

## Impact

- **New code:** `src/vgmdb_client/enrich/` (`models.py`, `backend.py`, `llm.py`, `errors.py`,
  `__init__.py`).
- **Dependencies:** none new (httpx already present); no `[llm]` extra yet.
- **Downstream:** provides the enriched output the B2 quality harness compares (parser vs ours+LLM).
