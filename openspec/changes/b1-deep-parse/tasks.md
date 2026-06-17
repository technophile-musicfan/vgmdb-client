## 1. Overlay model & error

- [ ] 1.1 Create `src/vgmdb_client/enrich/models.py` with `AlbumEnrichment` (`album_id: int`, `track_credits: dict[int, list[Credit]]`, `is_empty` property), frozen / `extra="forbid"`, reusing `Credit`/`ArtistRef`; and `errors.py` with `EnrichmentError(VgmdbClientError)`. Tests: empty vs populated, `is_empty`, model conventions

## 2. Backend protocol & helper

- [ ] 2.1 Define `EnrichmentBackend` protocol in `backend.py` (`enrich(album, raw_text) -> AlbumEnrichment`); implement `enrich_album(album, backend=None) -> AlbumEnrichment` in `__init__.py`/`_core` returning an empty `AlbumEnrichment` when `backend is None`, else `backend.enrich(album, album.notes or "")`
- [ ] 2.2 Tests: `enrich_album(album, None)` → empty; a stub backend's enrichment is returned and uses the album's notes as raw_text

## 3. OpenAI-compatible LLM backend

- [ ] 3.1 Implement `OpenAICompatibleBackend(url, model, api_key=None, timeout=...)` in `llm.py`: build a prompt from the tracklist + raw notes, POST OpenAI-compatible `/chat/completions` via httpx, parse the JSON content, apply `normalize_role(role_raw)` per credit, validate into `AlbumEnrichment`; raise `EnrichmentError` on transport/non-JSON/schema failure. Add `backend_from_env()` reading `LLM_URL`/`LLM_MODEL`/`LLM_API_KEY` (returns `None` when `LLM_URL` unset)
- [ ] 3.2 Tests via respx mocking `LLM_URL` `/chat/completions`: valid JSON content → `AlbumEnrichment` with `normalize_role` applied (use album 271 notes); malformed/non-JSON and transport error → `EnrichmentError`; `backend_from_env()` returns `None` without `LLM_URL` and a backend with it

## 4. Exports & conventions

- [ ] 4.1 Export `enrich_album`, `AlbumEnrichment`, `EnrichmentBackend`, `OpenAICompatibleBackend`, `backend_from_env`, `EnrichmentError` from `enrich/__init__.py`; run ruff, mypy, and the full test suite until green
