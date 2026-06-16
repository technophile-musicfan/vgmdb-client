## 1. Shared core (path builders)

- [x] 1.1 Create `src/vgmdb_client/client/_core.py` with `album_path(album_id) -> str` (`/album/{id}`) and `search_path(query) -> str` (`/search?q=<url-encoded>`, spaces→`+`); unit tests for both (incl. query encoding)

## 2. Synchronous Client

- [x] 2.1 Implement `Client` in `src/vgmdb_client/client/sync_client.py`: `__init__(config=None, *, transport=None)` (exactly one required, else `ValueError`; builds `SyncTransport(config)` otherwise), `get_album(id) -> Album` and `search(query) -> SearchResults` (via `_core` + `parse_album`/`parse_search`), `close()`, and `__enter__`/`__exit__`
- [x] 2.2 Tests with a `StubTransport` returning M5 fixture HTML by path: `get_album`/`search` equal the goldens; context manager closes the transport; `NotFoundError` and `ParseError` propagate; neither/both args → `ValueError`

## 3. Asynchronous AsyncClient

- [x] 3.1 Implement `AsyncClient` in `src/vgmdb_client/client/async_client.py`: same construction/lifecycle but `async get_album`/`search` (await `transport.get`), `aclose()`, `__aenter__`/`__aexit__`; reuse `_core` + parsers (no duplicated path/parse logic)
- [x] 3.2 Async tests with an async `StubTransport`: results equal the goldens and equal the sync client's; async context manager calls `aclose`; error propagation

## 4. Public API surface

- [x] 4.1 Export `Client`, `AsyncClient` from `client/__init__.py`; re-export the curated public surface (`Client`, `AsyncClient`, `TransportConfig`, M1 models + `Role`/`normalize_role`, error hierarchy) from `src/vgmdb_client/__init__.py`; test the top-level imports + `__all__`

## 5. Conventions & wiring

- [x] 5.1 Run ruff, mypy, and the full test suite; fix until green
