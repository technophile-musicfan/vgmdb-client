## 1. Dependency & package scaffold

- [x] 1.1 Add `lxml` as a runtime dependency (pyproject `dependencies`); create `src/vgmdb_client/parsers/` with `errors.py` (`ParseError(VgmdbClientError)`) and `__init__.py` exporting the public surface

## 2. Shared DOM helpers (_dom.py)

- [x] 2.1 Tree parse + whitespace-normalized text extraction helper
- [x] 2.2 `localized_text` from language spans implementing the placeholder rule (en→English; ja→Japanese only with real CJK script; ja-Latn→Romaji only when differing from English); unit tests
- [x] 2.3 Partial-date-from-text (via `PartialDate.parse`) and relative→absolute URL helpers; unit tests

## 3. parse_album

- [x] 3.1 Core fields (id, link, titles, catalog, release_date, classification, cover_small/full); single-disc/english-only fixture (271) green
- [x] 3.2 Discs + tracks (multi-disc, per-language track titles); CHRONO CROSS (4) green
- [x] 3.3 Credits (`role_raw` + `role = normalize_role(...)` + `ArtistRef`) and raw `notes`; multi-language/rich-credits fixtures (5012, 45000) green
- [x] 3.4 All remaining album fixtures green; resolve judgment-field divergences per-case (heuristic vs golden revision + B1 note)
- [x] 3.5 `ParseError` guard when essential album anchors are missing

## 4. parse_search

- [x] 4.1 Query from results header + result rows → `AlbumSearchResult`; near-empty (0) and multi-hit (first-10) green; correct multi-hit golden `query` to the displayed form
- [x] 4.2 `ParseError` guard when the results container is missing

## 5. Conventions & wiring

- [x] 5.1 Export `parse_album`, `parse_search`, `ParseError`; run ruff, mypy, and the full test suite; fix until green
