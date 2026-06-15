## 1. Value types (common.py)

- [ ] 1.1 Implement `LocalizedText` (`RootModel[dict[str, str]]`) with `prefer(*langs)`, `default`, `all`, `__str__`; test prefer hit/fallback, default English/Romaji preference, empty→None
- [ ] 1.2 Implement `PartialDate` (year + optional month/day) with range validation, day-requires-month rule, `precision`, `__str__`; test valid/invalid construction and rendering per precision
- [ ] 1.3 Add `PartialDate.parse` classmethod for `YYYY` / `YYYY-MM` / `YYYY-MM-DD`; test round-trips and `None` on unparseable input
- [ ] 1.4 Implement `ArtistRef` (names: LocalizedText, id/link optional); test construction with and without id/link

## 2. Album entity (album.py)

- [ ] 2.1 Implement `Track` (titles, number?, length?) and `Disc` (number?, name?, tracks); test construction and defaults
- [ ] 2.2 Implement `Credit` (role, artists: list[ArtistRef]); test open-ended role + artist list
- [ ] 2.3 Implement `Album` core subset (id, link?, titles, catalog?, release_date?, classification?, cover_small?, cover_full?, discs, credits, notes?); test full and partial construction (optional defaults applied)

## 3. Search models (search.py)

- [ ] 3.1 Implement `AlbumSearchResult` (id, link?, titles, catalog?, release_date?) and `SearchResults` (query, albums); test construction and that results carry album entries

## 4. Conventions & wiring

- [ ] 4.1 Apply `model_config = ConfigDict(extra="forbid", frozen=True)` to all models; test mutation rejected and unknown field rejected
- [ ] 4.2 Export the public model surface from `models/__init__.py` (and re-export from the package as appropriate); test imports
- [ ] 4.3 Run ruff, mypy, and the full test suite; fix until green
