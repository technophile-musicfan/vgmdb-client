## Context

vgmdb-client fetches pages directly from `vgmdb.net`, which is behind Cloudflare and offers no
API. The transport is the foundational network layer that every higher layer (M3 parsers, M4
client) depends on. The project currently has empty `src/`/`tests/` and no runtime dependencies.

Source of truth for this design: `docs/superpowers/vgmdb_client/2026-06-14_transport_design.md`.

Constraints:
- Both a sync and an async client are required (vision: shared core, no duplicated logic).
- Public data models use pydantic v2 across the library, so config should too.
- MVP supplies the `cf_clearance` token manually; obtaining it (browser automation) is V1a.

## Goals / Non-Goals

**Goals:**
- A low-level `get(path) -> str` returning raw HTML, with no knowledge of vgmdb URL structure or
  parsing.
- Sync and async clients sharing one sans-I/O core for request assembly, response classification,
  retry policy, and throttle timing.
- Typed error classification that distinguishes a Cloudflare challenge from a real 404, plus
  rate-limit and transient categories.
- Retry transient failures only; throttle requests politely; refresh credentials live.

**Non-Goals:**
- Obtaining/renewing `cf_clearance` via a browser (Playwright/stealth) — V1a (`vgmdb-0e5.1`).
- URL/endpoint construction — M4 (`vgmdb-v9g.7`).
- HTML parsing — M3 (`vgmdb-v9g.6`).
- Auto-handling `429` (sleeping `Retry-After` and retrying) — surfaced to the caller instead.

## Decisions

**D1 — Low-level generic `get(path)`, not typed endpoints.**
Transport stays parser-agnostic and reusable; M4 owns vgmdb URL layout. *Alternative:* typed
`fetch_album_html(id)` methods — rejected because it couples transport to vgmdb specifics and
overlaps M4.

**D2 — Shared sans-I/O core.**
A pure `core.py` holds `classify_response`, request assembly, the retry predicate, and throttle
wait-time math; `SyncTransport`/`AsyncTransport` wrap `httpx.Client`/`httpx.AsyncClient` and add
only the `await`. This makes the hard logic unit-testable without network and guarantees sync and
async behave identically. *Alternative:* two independent implementations — rejected (drift,
duplicated tests).

**D3 — Return `str`, signal status via exceptions.**
`get()` returns the decoded HTML body; the parser needs only text. Status/category is conveyed by
typed errors rather than a result wrapper. *Alternative:* a `FetchResult` object — rejected as
YAGNI for MVP.

**D4 — tenacity for retries.**
Declarative, battle-tested backoff. The retry predicate fires **only** on
`TransientTransportError`; Cloudflare challenge, 404, and 429 are never retried. *Alternative:* a
hand-rolled loop or httpx transport-level retries (connection-only) — rejected for less control /
insufficient coverage.

**D5 — Cloudflare detection by layered signals.**
`classify_response` checks, in order: `404 → NotFoundError`; `403/503` + Cloudflare markers
(`cf-mitigated: challenge`, else body signature corroborated by `server: cloudflare`/`cf-ray`) →
`CloudflareChallengeError`; `429 → RateLimitedError`; other `5xx`/timeout/conn →
`TransientTransportError`; `2xx → text`. Heuristics are hardened against real captured pages in M5.

**D6 — Optional politeness throttle, default 1.0s.**
A per-transport gate enforces `min_interval` between request starts in both clients to protect the
`cf_clearance` token from rate-bans during bulk fetches; `0` disables. *Alternative:* defer
throttling — rejected; cheap insurance now.

**D7 — pydantic `TransportConfig`, stdlib `logging`.**
Config is a pydantic v2 model (consistent with library models). Logging uses stdlib `logging`
(module logger) rather than `structlog`, to avoid forcing a logging framework on consumers.

**D8 — New runtime deps `httpx`, `tenacity`, `pydantic`; dev dep `respx`.**
First runtime deps for the project. Tests use `httpx.MockTransport`/`respx` — no live network.

## Risks / Trade-offs

- **Cloudflare HTML markers drift / false negatives** → Layer header + body signals; lock down
  against real captured challenge pages in M5 fixtures; keep `CloudflareChallengeError` messaging
  actionable (refresh token).
- **Misclassifying a challenge as transient causes futile retries** → challenge detection runs
  before the transient bucket; challenges are explicitly excluded from the retry predicate.
- **Throttle on by default may surprise users expecting raw speed** → documented and configurable;
  `min_interval=0` fully disables.
- **Sync/async divergence** → mitigated structurally by D2 (single core) plus sync/async parity
  tests.

## Open Questions

- Final Cloudflare body signatures depend on real captured pages (resolved in M5).
- Whether to later add opt-in auto-handling of `429` (sleep `Retry-After` and retry) if bulk use
  makes manual handling painful — deferred, not in this change.
