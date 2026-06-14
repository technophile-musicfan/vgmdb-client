# M2 Transport — Feature Design

**Date:** 2026-06-14
**Status:** Design (Workflow 2, step 1)
**Epic:** `vgmdb-v9g.4` (M2 Transport) — parent `vgmdb-v9g` (MVP)
**Major scope:** `vgmdb_client`
**Vision:** `docs/superpowers/2026-06-14_vgmdb_client.md`

## Purpose

Transport is the **only layer that performs network I/O**. Given a path, it performs an
authenticated HTTP GET against `vgmdb.net`, handles the Cloudflare / retry / throttle realities,
and returns the page's **raw HTML text** — or raises a typed error. It knows nothing about
vgmdb URL structure (M4 Client builds paths) and nothing about parsing (M3 Parsers).

One sentence: *given a path, return the page's HTML or raise a typed error.*

## Scope

**In scope**
- `httpx`-based sync **and** async clients over a shared sans-I/O core.
- Manual injection of a caller-supplied `cf_clearance` cookie + matching `User-Agent`.
- Live refresh of token/UA without rebuilding the client (hook for V1a auth helper).
- Retry of transient failures (tenacity); never retry a Cloudflare challenge, 404, or 429.
- Typed-error classification distinguishing Cloudflare challenge vs 404 vs rate-limit vs transient.
- Optional politeness throttle (min-interval between requests).

**Out of scope (tracked elsewhere)**
- Obtaining/renewing the `cf_clearance` token via a browser (Playwright/stealth) → **V1a** `vgmdb-0e5.1`.
- URL/endpoint construction for albums/search → **M4** `vgmdb-v9g.7`.
- HTML parsing → **M3** `vgmdb-v9g.6`.

## Public surface

```python
class SyncTransport:
    def __init__(self, config: TransportConfig): ...
    def get(self, path: str) -> str            # returns HTML text; raises typed errors
    def set_cf_clearance(self, token: str) -> None
    def set_user_agent(self, ua: str) -> None
    def close(self) -> None                     # also a sync context manager

class AsyncTransport:                            # identical surface, async variants
    def __init__(self, config: TransportConfig): ...
    async def get(self, path: str) -> str
    def set_cf_clearance(self, token: str) -> None
    def set_user_agent(self, ua: str) -> None
    async def aclose(self) -> None              # also an async context manager
```

`get()` returns a plain `str` (decoded HTML body). No wrapper object — the parser layer only
needs the text, and status information is conveyed through exceptions.

### TransportConfig (pydantic v2)

| Field | Default | Meaning |
|-------|---------|---------|
| `base_url` | `https://vgmdb.net` | Root URL; `get(path)` is joined against it. |
| `user_agent` | — (required) | `User-Agent` header; must match the browser the `cf_clearance` was issued for. |
| `cf_clearance` | `None` | Cloudflare clearance cookie value, injected as the `cf_clearance` cookie. |
| `timeout` | `10.0` | Per-request timeout (seconds). |
| `max_retries` | `3` | Max retry attempts for transient failures. |
| `backoff_base` | `0.5` | Exponential backoff base (seconds). |
| `backoff_max` | `8.0` | Backoff ceiling (seconds). |
| `min_interval` | `1.0` | Politeness throttle: min seconds between request starts. `0` disables. |
| `proxy` | `None` | Optional proxy URL passed through to httpx. |

`set_cf_clearance` / `set_user_agent` mutate the live httpx client's cookie/header so V1a's
auth helper can refresh a stale token mid-session without reconstructing the transport.

## Shared sync/async core (no duplicated logic)

A **sans-I/O** core module (`core.py`) holds everything pure; the sync/async classes are thin
wrappers whose only difference is `await`:

- `classify_response(status, headers, text) -> None | raises` — single source of truth for
  OK / Cloudflare-challenge / 404 / rate-limited / transient. Pure, fully unit-testable.
- request assembly — URL join + header/cookie construction (pure).
- tenacity retry predicate — retry **only** `TransientTransportError`.
- throttle wait-time calculation — pure; only the actual sleep differs (`time.sleep` vs
  `asyncio.sleep`).

`SyncTransport` wraps `httpx.Client`; `AsyncTransport` wraps `httpx.AsyncClient`. Both call into
`core.py`.

## Cloudflare-challenge vs 404 detection

`classify_response` decides in order:

1. **404** → `NotFoundError` (app-level "no such resource").
2. **403 / 503 with Cloudflare markers** → `CloudflareChallengeError` (**not** retried — a
   missing/stale token will not resolve by retrying). Markers, in priority:
   - `cf-mitigated: challenge` response header; otherwise
   - body signatures (`Just a moment…`, `cf-chl`, challenge-platform script), corroborated by
     `server: cloudflare` / presence of `cf-ray`.
3. **429** → `RateLimitedError` (honor `Retry-After`; **not** auto-retried in M2).
4. **other 5xx / timeouts / connection errors** → `TransientTransportError` (retried).
5. **2xx** → return body text.

These heuristics are hardened against real captured challenge/404 pages in **M5 fixtures**.

## Error hierarchy

```
VgmdbClientError                 # library-wide base (top-level errors.py; reused by M3/M4)
└── TransportError
    ├── CloudflareChallengeError # not retried; signals "refresh token" (→ V1a)
    ├── NotFoundError            # 404
    ├── RateLimitedError         # 429, carries retry_after
    └── TransientTransportError  # 5xx/timeout/conn; retried; re-raised if retries exhausted
```

`CloudflareChallengeError` carries a clear message pointing the user to supply/refresh
`cf_clearance`. `RateLimitedError` exposes `retry_after` (parsed from the header when present).

## Retries & throttle

- **tenacity**: retry `TransientTransportError` only, exponential backoff (`backoff_base`)
  with jitter, capped at `backoff_max` and `max_retries`. Cloudflare-challenge, 404, and
  rate-limit are never retried. When retries are exhausted, the last `TransientTransportError`
  propagates.
- **Throttle**: a per-transport gate enforcing `min_interval` between request *starts*, applied
  in both sync and async. Default `1.0s` (set `0` to disable) to protect the `cf_clearance`
  token from rate-bans during bulk fetches.

## Dependencies & logging

- **Runtime (new for the project):** `httpx`, `tenacity`, `pydantic`.
- **No** Playwright/stealth in M2 (deferred to V1a).
- **Logging:** stdlib `logging` (module-level logger), not `structlog`, to avoid forcing a
  logging framework on consumers. Debug-level per-request logs (method, path, status, attempt).

## Module layout

```
src/vgmdb_client/
  errors.py                 # VgmdbClientError base
  transport/
    __init__.py             # exports SyncTransport, AsyncTransport, TransportConfig, errors
    config.py               # TransportConfig
    errors.py               # TransportError + subclasses
    core.py                 # sans-I/O: classify_response, request build, retry predicate, throttle calc
    sync_client.py          # SyncTransport
    async_client.py         # AsyncTransport
```

## Testing strategy (no live network)

Use `httpx.MockTransport` to inject canned responses, with `respx` (dev dependency) for
ergonomic request mocking. Coverage:

- `classify_response` truth table: 200 OK, 404, 403+CF markers, 503+CF markers, 429, generic 5xx.
- Retry behavior: transient → retried up to `max_retries`; Cloudflare-challenge / 404 / 429 →
  **not** retried; exhausted retries re-raise `TransientTransportError`.
- Throttle: `min_interval` enforced between consecutive requests (monkeypatched clock); `0`
  disables.
- Header/cookie injection: `cf_clearance` cookie + `User-Agent` present; `set_*` refresh works.
- Sync/async parity: equivalent behavior for both clients.

## Acceptance criteria (from the epic)

- Sync **and** async fetch of a vgmdb URL with injected `cf_clearance` / `User-Agent`.
- Retry on transient failure.
- Distinct exception types for Cloudflare challenge vs 404.

## Open questions / deferrals

- **Auto-handling 429** (sleep `Retry-After` and retry) is deliberately out of M2 — surfaced as
  `RateLimitedError` for the caller. Revisit if bulk use makes it painful.
- Exact Cloudflare body signatures will be finalized against real captured pages in M5.
