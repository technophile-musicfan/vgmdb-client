## Why

The B2 quality harness reports the ours+LLM enrichment column as *coverage only* ("N tracks gained
credits"), because we never authored per-track-credit ground truth. As a result we cannot **score**
or **compare** enrichment backends — exactly what is needed to judge an LLM, a prompt variant, or the
planned lightweight backend. This cycle adds the ground truth and the scoring, and makes the harness
rank multiple named backends. It is the enabling first cycle of the Enrichment v2 epic (vgmdb-zsy).

## What Changes

- **fixtures**: add hand-authored per-track-credit enrichment goldens under
  `tests/fixtures/vgmdb/enrichment/<album_id>.json`, one per album fixture — populated from the
  album's freeform notes where credits are clearly track-attributed, **empty** (negative ground
  truth) otherwise — each validated against `AlbumEnrichment` on load. Add loaders
  `load_enrichment_golden(album_id)` and `iter_enrichment_goldens()`.
- **benchmark**: add a credit-matching scorer (`benchmarks/quality/enrichment.py`) producing
  precision / recall / F1 against an enrichment golden; extend the harness `run()` to accept a
  mapping of **named** backends and add an "Enrichment quality" report section ranking them. The
  existing coverage section stays.

No new enrichment backends this cycle (they are Cycles 2–3); the scoring is exercised with stub
backends, so CI needs no network or Docker. No change to `AlbumEnrichment` or the
`EnrichmentBackend` protocol.

## Capabilities

### New Capabilities
<!-- None: extends existing capabilities. -->

### Modified Capabilities
- `fixtures`: add committed per-album enrichment goldens + their loaders.
- `benchmark`: add enrichment scoring (precision/recall/F1) and multi-named-backend reporting.

## Impact

- New golden files under `tests/fixtures/vgmdb/enrichment/`; new loader functions in
  `tests/support/fixtures.py`.
- New `benchmarks/quality/enrichment.py`; changes to `benchmarks/quality/run.py` and `report.py`
  (dev-only, excluded from the wheel).
- New unit + smoke tests. No runtime/`src` behavior change; no new dependency.
