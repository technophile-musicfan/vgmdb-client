# M4 Client API — Feature Design

**Date:** 2026-06-16
**Status:** Design (Workflow 2, step 1)
**Epic:** `vgmdb-v9g.7` (M4 Client API) — parent `vgmdb-v9g` (MVP)
**Major scope:** `vgmdb_client`
**Vision:** `docs/superpowers/2026-06-14_vgmdb_client.md`
**Depends on:** M2 Transport (merged), M3 Parsers (merged), M1 Models (merged)

## Purpose

The public API: a synchronous `Client` and an asynchronous `AsyncClient` that compose the transport
(M2) and parsers (M3) over a shared core, exposing `get_album(id) -> Album` and
`search(query) -> SearchResults` that return validated M1 models. No duplicated parsing/path logic
between sync and async.

## Scope

**In scope**
- `Client` (sync) and `AsyncClient` (async) with `get_album(id)` and `search(query)`.
- A shared core (path builders) so sync/async differ only by `await`.
- Config-object construction (`TransportConfig`) + transport injection (for tests/advanced use).
- Context-manager lifecycle (`close`/`aclose`).
- A curated top-level public surface re-exported from `vgmdb_client`.

**Out of scope (tracked elsewhere)**
- Caching, client-level retries (the transport owns retry/throttle).
- Auth/token-refresh helper → V1 (`vgmdb-0e5`).
- Entities beyond album + search → B3 (`vgmdb-bzf.3`).
- No schema/model changes.

## Decisions

**D1 — `client/` package.** `src/vgmdb_client/client/`: `_core.py` (shared path builders),
`sync_client.py` (`Client`), `async_client.py` (`AsyncClient`), `__init__.py` (exports). Mirrors the
existing `transport/`/`parsers/` package layout.

**D2 — Shared core = path builders; parsing already shared.** `_core.py`:
`album_path(album_id) -> "/album/{album_id}"` and `search_path(query) -> "/search?q={quote_plus(query)}"`.
The parse step is the existing pure `parse_album`/`parse_search`. So each client method is two lines and
the only sync/async difference is `await` — there is no duplicated parsing or path logic. *Alternative:*
a generic core parameterized by a fetch callable — rejected as over-engineering for two one-line methods.

**D3 — Construction: config object + transport injection.** `Client(config: TransportConfig)` builds a
`SyncTransport(config)`; `Client(config=None, *, transport=...)` injects a ready transport (used by tests
and advanced callers). Exactly one of `config`/`transport` must be provided (else `ValueError`).
`AsyncClient` is analogous with `AsyncTransport`. *Alternatives:* convenience kwargs (re-declares
`TransportConfig`'s fields — duplication) and injection-only (two construction paths) — rejected.

**D4 — Lifecycle via context managers.** `Client` is a sync context manager (`__enter__`/`__exit__`) plus
`close()`, delegating to `transport.close()`. `AsyncClient` is an async context manager
(`__aenter__`/`__aexit__`) plus `aclose()`, delegating to `transport.aclose()`.

**D5 — Errors propagate unchanged.** The client adds no error semantics: transport's typed errors
(`CloudflareChallengeError`, `NotFoundError`, `RateLimitedError`, `TransientTransportError`,
`TransportError`) and `ParseError` surface directly from `get_album`/`search`.

**D6 — Curated top-level public API.** `vgmdb_client/__init__.py` re-exports: `Client`, `AsyncClient`,
`TransportConfig`, the M1 models (`Album`, `AlbumSearchResult`, `ArtistRef`, `Credit`, `Disc`,
`LocalizedText`, `PartialDate`, `Role`, `SearchResults`, `Track`, `normalize_role`), and the error
hierarchy (`VgmdbClientError`, `ParseError`, `TransportError`, `CloudflareChallengeError`,
`NotFoundError`, `RateLimitedError`, `TransientTransportError`). Enables `from vgmdb_client import
Client, Album, NotFoundError`.

## Data flow

```
get_album(id):  album_path(id)  ─▶ transport.get(path) ─▶ parse_album(html)  ─▶ Album
search(query):  search_path(q)  ─▶ transport.get(path) ─▶ parse_search(html) ─▶ SearchResults
            (AsyncClient awaits transport.get; everything else identical)
```

## Testing

- A test `StubTransport` whose `.get(path)` returns M5 fixture HTML keyed by path (album/search),
  injected via `Client(transport=stub)` / `AsyncClient(transport=async_stub)`.
- `get_album`/`search` return the golden models (reusing the M5 fixtures + loader), sync and async.
- Path-builder unit tests (`album_path`, `search_path` incl. query encoding).
- Context-manager closes the transport (sync `close`, async `aclose`) — both.
- Error propagation: stub raising `NotFoundError` surfaces from `get_album`; non-album HTML →
  `ParseError`.
- A "sync and async agree" test from the same fixture (shared-core, no divergence).
- Construction guard: neither/both of `config`/`transport` → `ValueError`.
- `ruff`, `mypy`, full suite green.

## Risks / Trade-offs

- **Sync/async duplication of the two-line method bodies** is unavoidable (different `await`); the shared
  core keeps the only real logic (paths + parsing) in one place, so the duplication is trivial and safe.
- **Search-result first-N caveat** lives in the parser/fixtures, not the client; `search` returns whatever
  the parser yields for the page.

## Acceptance criteria (from the epic)

- `Client.get_album`/`search` and `AsyncClient` equivalents return validated models; shared core; both
  covered by tests.

## Open questions / deferrals

- A convenience constructor (e.g. `Client.from_token(...)`) could be added later; deferred (the config
  object is the one settings home for now).
