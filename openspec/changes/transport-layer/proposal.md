## Why

vgmdb-client must fetch pages directly from `vgmdb.net`, which sits behind Cloudflare and
exposes no API. Every higher layer (parsers, client) needs a single, reliable way to perform
authenticated HTTP GETs that distinguishes a Cloudflare challenge from a genuine 404 and retries
only failures worth retrying. This is the foundational network layer — nothing else can be built
or tested against live vgmdb without it.

## What Changes

- Introduce a **transport layer** providing both a `SyncTransport` and an `AsyncTransport` over a
  shared sans-I/O core (no duplicated logic).
- Expose a low-level `get(path) -> str` that returns raw HTML; URL/endpoint construction stays in
  the Client layer (M4) and parsing in the Parser layer (M3).
- Inject a caller-supplied `cf_clearance` cookie and matching `User-Agent`; allow live refresh of
  both via `set_cf_clearance` / `set_user_agent` (hook for the future V1a auth helper).
- Classify responses into typed errors: Cloudflare challenge, 404 not-found, 429 rate-limited, and
  transient — distinguishing a Cloudflare challenge from a real 404.
- Retry **only** transient failures via tenacity (exponential backoff + jitter); never retry a
  Cloudflare challenge, 404, or rate-limit.
- Apply an optional politeness throttle (configurable min-interval between requests) in both sync
  and async clients to protect the token from rate-bans.
- Add the project's first runtime dependencies: `httpx`, `tenacity`, `pydantic`.

Out of scope (tracked separately): obtaining/renewing the `cf_clearance` token via a browser
(V1a), URL construction (M4), and HTML parsing (M3).

## Capabilities

### New Capabilities
- `transport`: Authenticated, Cloudflare-aware HTTP transport for `vgmdb.net` — sync + async
  `get(path) -> str` over a shared core, typed error classification (Cloudflare challenge vs 404
  vs rate-limit vs transient), tenacity-based retry of transient failures only, manual
  `cf_clearance`/`User-Agent` injection with live refresh, and an optional politeness throttle.

### Modified Capabilities
<!-- None — this is the first capability in the project. -->

## Impact

- **New code:** `src/vgmdb_client/errors.py` (library-wide base error) and a new
  `src/vgmdb_client/transport/` package (`config.py`, `errors.py`, `core.py`, `sync_client.py`,
  `async_client.py`, `__init__.py`).
- **Dependencies:** adds runtime deps `httpx`, `tenacity`, `pydantic`; adds dev dep `respx` for
  HTTP mocking in tests.
- **Downstream:** unblocks M4 Client (`vgmdb-v9g.7`) and V1a auth helper (`vgmdb-0e5.1`), which
  consume this transport.
- **No** browser-automation dependencies (Playwright/stealth) are introduced here.
