## 1. Enrichment goldens

- [x] 1.1 Inspect each album fixture's `notes`; hand-author `tests/fixtures/vgmdb/enrichment/<id>.json`
  (serialized `AlbumEnrichment`) — real per-track credits where the notes attribute them to a track
  (e.g. 271), empty `{"album_id": N, "track_credits": {}}` otherwise.
- [x] 1.2 `tests/support/fixtures.py`: `load_enrichment_golden(album_id) -> AlbumEnrichment` (validates
  on load) + `iter_enrichment_goldens()`. Test: every album fixture has a loadable golden.

## 2. Credit-matching scorer

- [x] 2.1 `benchmarks/quality/enrichment.py`: credit identity `(track number, normalized Role,
  frozenset casefolded artist names)`; `score_enrichment(produced, golden) -> (precision, recall, f1)`
  with the zero-denominator = 1.0 rule.
- [x] 2.2 Unit-test the scorer: exact match (1/1/1), partial recall, hallucination vs empty golden
  (precision < 1), role mismatch, artist-name-overlap match, empty-vs-empty perfect, F1 math.

## 3. Multi-backend harness + report

- [x] 3.1 `benchmarks/quality/run.py`: `run()` takes `backends: dict[str, EnrichmentBackend]`; per
  album load its enrichment golden and score each backend's `enrich_album` output. `backend_from_env()`
  supplies `{"llm": ...}` when `LLM_URL` is set, else `{}`.
- [x] 3.2 `benchmarks/quality/report.py`: "Enrichment quality" section (backend × P/R/F1 aggregate +
  per-album) and stdout scorecard; keep the coverage section.

## 4. Tests + gate

- [x] 4.1 Smoke test: run the harness over fixtures with stub backends (one "perfect" returning the
  golden, one "empty"), no network — assert the enrichment scorecard appears and the perfect stub
  scores recall 1.0 on a populated album, the empty stub precision 1.0.
- [x] 4.2 Full gate (ruff + mypy + pytest) green.
