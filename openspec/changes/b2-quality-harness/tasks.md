## 1. Canonical record + adapters

- [ ] 1.1 `benchmarks/quality/fields.py`: canonical field set (album title/catalog/release_date/
  publisher/label + `disc{d}.track{t}.title`) and per-field normalizers (text strip+casefold,
  LocalizedText→default, PartialDate→ISO). Unit-test the normalizers.
- [ ] 1.2 `benchmarks/quality/adapters.py`: `from_album(Album)`, `from_golden(Album)`,
  `from_hufman(dict)` (tolerant — missing keys → missing value). Unit-test each, incl. a hufman
  response missing a field.

## 2. Scoring + comparison

- [ ] 2.1 `benchmarks/quality/compare.py`: per-field scoring vs golden ({match, mismatch, missing,
  extra}) using the normalizers; build the raw N-way diff rows. Unit-test match/mismatch/missing.
- [ ] 2.2 Enrichment coverage in `compare.py`: per album, tracks-with-credits / total + total
  credits; "n/a" when no backend. Unit-test backend-present and no-backend paths.

## 3. hufman client + runner + report

- [ ] 3.1 `benchmarks/quality/hufman_client.py`: httpx GET `HUFMAN_URL` (default
  `http://localhost:5000`) → album JSON dict or `None` when unreachable. Unit-test unreachable→None
  (respx) and URL-from-env.
- [ ] 3.2 `benchmarks/quality/report.py`: render Markdown (scorecard + coverage + per-album N-way
  diff) and the stdout summary. Unit-test the report contains the expected sections.
- [ ] 3.3 `benchmarks/quality/run.py`: entry point — iterate fixtures → parse ours → enrich
  (optional) → fetch hufman (optional) → compare → write report + print summary.

## 4. Test + gate

- [ ] 4.1 Smoke test under `tests/`: run the harness over the fixtures with hufman disabled + no LLM
  backend (no Docker/network), assert a report with the expected ours-vs-golden scorecard rows is
  produced and the run completes clean.
- [ ] 4.2 `.gitignore` the generated `benchmarks/quality/report.md`. Run the full gate
  (ruff + mypy + pytest) green.
