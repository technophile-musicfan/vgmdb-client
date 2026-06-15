## 1. Dataset scaffold & dev dependency

- [ ] 1.1 Add `python-dotenv` as a **dev** dependency (pyproject dev/test group); confirm the runtime dependency set is unchanged
- [ ] 1.2 Create the `tests/fixtures/vgmdb/` layout (`albums/`, `search/`) and a `README.md` documenting source (vgmdb.net), purpose (testing), capture date placeholder, and ToS/attribution note
- [ ] 1.3 Create an initial `manifest.json` with the chosen album ids + 2 search queries, each tagged with its diversity dimension, source URL, and (placeholder) captured date

## 2. Capture script (dev-only)

- [ ] 2.1 Implement `scripts/capture_fixtures.py`: load `.env` via `python-dotenv` (`VGMDB_CF_CLEARANCE`, `VGMDB_USER_AGENT`, optional `VGMDB_BASE_URL`), read targets from `manifest.json`, fetch via `SyncTransport` (throttle on), write only `albums/<id>.html` / `search/<slug>.html`
- [ ] 2.2 Add `--overwrite` handling (skip existing HTML by default) and clear transport-error surfacing (e.g. `CloudflareChallengeError` → token-refresh message); ensure the script is excluded from the shipped package and not run in CI

## 3. Capture the seed HTML

- [ ] 3.1 Run the capture script with a valid `.env` to fetch all manifest targets (~10+ album pages + 2 search pages); commit the raw HTML and update captured dates in the manifest

## 4. Author golden outputs (by hand, from HTML)

- [ ] 4.1 Transcribe golden `Album` JSON (`model_dump(mode="json")`) for each album fixture by reading the captured HTML directly (no parser); chunk across the album set
- [ ] 4.2 Transcribe golden `SearchResults` JSON for each search fixture the same way
- [ ] 4.3 Human review pass: verify each golden against the rendered page for transcription errors (track titles, catalog, dates, credits)

## 5. Loader & well-formedness tests

- [ ] 5.1 Implement `tests/support/fixtures.py`: `iter_album_fixtures()`, `load_album_fixture(id) -> (str, Album)`, and the search equivalents (golden via `model_validate_json`)
- [ ] 5.2 Tests: every golden validates against its M1 model (round-trip)
- [ ] 5.3 Tests: manifest entries match files on disk (no orphans, no missing)
- [ ] 5.4 Tests: each captured HTML file is present and non-empty

## 6. Conventions & wiring

- [ ] 6.1 Run ruff, mypy, and the full test suite; fix until green
