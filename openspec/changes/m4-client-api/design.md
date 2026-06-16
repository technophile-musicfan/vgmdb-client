## Context

M2 transport (`SyncTransport`/`AsyncTransport`, `.get(path) -> str`, `TransportConfig`,
`close`/`aclose`) and M3 parsers (`parse_album`/`parse_search`, pure) are merged; nothing composes
them into a usable API. M4 adds the public `Client`/`AsyncClient`. Source of truth:
`docs/superpowers/vgmdb_client/2026-06-16_client_api_design.md`. No schema changes.

## Goals / Non-Goals

**Goals:**
- `Client` (sync) and `AsyncClient` (async) with `get_album(id)` and `search(query)`.
- A shared core so sync/async differ only by `await`.
- Config-object construction + transport injection; context-manager lifecycle.
- A curated top-level public surface.

**Non-Goals:**
- Caching, client-level retries (transport owns retry/throttle).
- Auth/token-refresh helper — V1; entities beyond album+search — B3.
- Any model/schema change.

## Decisions

**D1 — `client/` package** mirroring `transport/`/`parsers/`: `_core.py`, `sync_client.py`,
`async_client.py`, `__init__.py`.

**D2 — Shared core = path builders.** `album_path(id) -> "/album/{id}"`,
`search_path(query) -> "/search?q={quote_plus(query)}"`. Parsing is the existing pure
`parse_album`/`parse_search`. Each method is two lines; the only sync/async difference is `await`.
*Alternative:* a fetch-callable-parameterized core — rejected (over-engineering).

**D3 — Construction: config object + injection.** `Client(config: TransportConfig)` builds
`SyncTransport(config)`; `Client(config=None, *, transport=...)` injects. Exactly one of
`config`/`transport` (else `ValueError`). `AsyncClient` analogous with `AsyncTransport`.

**D4 — Context-manager lifecycle.** `Client.__enter__/__exit__` + `close()` -> `transport.close()`;
`AsyncClient.__aenter__/__aexit__` + `aclose()` -> `transport.aclose()`.

**D5 — Errors propagate unchanged.** Transport typed errors + `ParseError` surface from the methods;
the client adds no new error semantics (e.g. missing album -> `NotFoundError`).

**D6 — Curated top-level re-exports** from `vgmdb_client/__init__.py`: `Client`, `AsyncClient`,
`TransportConfig`, M1 models + `Role`/`normalize_role`, and the error hierarchy.

## Data flow

```
get_album(id):  album_path(id)  -> transport.get -> parse_album  -> Album
search(query):  search_path(q)  -> transport.get -> parse_search -> SearchResults
            (AsyncClient awaits transport.get; otherwise identical)
```

## Risks / Trade-offs

- **Two-line method duplication across sync/async** is unavoidable (the `await`); the shared core keeps
  paths + parsing in one place, so the duplication is trivial and safe.
- **Top-level re-export surface** must stay in sync with the models/errors it lists; a `__all__` test
  guards the public names.

## Migration Plan

Additive — a new package plus curated re-exports in the previously near-empty top-level `__init__`.
No changes to transport, parsers, or models.

## Open Questions

- A `Client.from_token(...)` convenience constructor could be added later; deferred.
