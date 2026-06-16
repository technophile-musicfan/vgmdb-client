## Why

The transport (M2) fetches HTML and the parsers (M3) turn HTML into models, but nothing yet composes
them into a usable public API. M4 adds the sync `Client` and async `AsyncClient` — the MVP's public
entry point — exposing `get_album(id)` and `search(query)` that return validated M1 models, with no
duplicated parsing/path logic between sync and async.

## What Changes

- Add a **`client` package** (`src/vgmdb_client/client/`):
  - `_core.py` — shared path builders: `album_path(id)`, `search_path(query)` (query URL-encoded).
  - `sync_client.py` — `Client` with `get_album(id) -> Album`, `search(query) -> SearchResults`.
  - `async_client.py` — `AsyncClient` with the async equivalents.
- **Construction:** `Client(config: TransportConfig)` builds a `SyncTransport`; `Client(config=None,
  *, transport=...)` injects a ready transport (tests/advanced). Exactly one of `config`/`transport`
  required. `AsyncClient` is analogous with `AsyncTransport`.
- **Lifecycle:** `Client` is a context manager + `close()`; `AsyncClient` is an async context manager
  + `aclose()`; both delegate to the transport.
- **Errors propagate unchanged:** transport's typed errors and `ParseError` surface from the methods.
- **Curated top-level public API:** re-export from `vgmdb_client/__init__.py` — `Client`,
  `AsyncClient`, `TransportConfig`, the M1 models + `normalize_role`/`Role`, and the error hierarchy.

Out of scope (tracked separately): caching and client-level retries (transport owns retry/throttle);
auth/token-refresh helper → V1 (`vgmdb-0e5`); entities beyond album+search → B3 (`vgmdb-bzf.3`). No
schema/model changes.

## Capabilities

### New Capabilities
- `client`: The public sync `Client` and async `AsyncClient` composing transport + parsers over a
  shared core — `get_album(id) -> Album` and `search(query) -> SearchResults` returning validated M1
  models, with config-object construction + transport injection, context-manager lifecycle, and
  pass-through error semantics.

### Modified Capabilities
<!-- None — `transport`, `parsers`, and `models` are composed unchanged. The top-level package
     __init__ re-export is a packaging concern, not a spec-level change to those capabilities. -->

## Impact

- **New code:** `src/vgmdb_client/client/` (`_core.py`, `sync_client.py`, `async_client.py`,
  `__init__.py`); `src/vgmdb_client/__init__.py` gains the curated re-exports.
- **Dependencies:** none new — composes existing M1/M2/M3.
- **Public API:** `from vgmdb_client import Client, Album, NotFoundError` becomes the entry point;
  unblocks V1 work.
