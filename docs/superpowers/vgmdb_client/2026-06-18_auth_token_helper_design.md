# V1a Auth-token helper — Design

**Date:** 2026-06-18
**Status:** Design (Workflow 2, brainstorm)
**Major scope:** `vgmdb_client`
**Epic:** `vgmdb-0e5.1` (V1a Auth-token helper), under `vgmdb-0e5` (V1: complete & polished)
**Builds on:** M2 Transport (`vgmdb-v9g.4`)

## Problem

`vgmdb.net` sits behind Cloudflare. A request only succeeds when it carries a valid
`cf_clearance` cookie **paired with the exact `User-Agent`** the token was issued for (the
token is bound to that UA and the client IP). The transport already injects both and exposes
`set_cf_clearance` / `set_user_agent`, and raises a non-retried `CloudflareChallengeError` when
the token is missing or stale. What is missing is the *human-facing* step: helping the user get
a fresh `(cf_clearance, User-Agent)` pair out of their own already-solved browser session and
into the client, and re-applying a fresh pair when the old one expires.

**Explicit non-goal:** this helper does NOT defeat, solve, or automate the Cloudflare challenge.
The human passes the challenge in their own browser; the helper only transports the resulting
credentials.

## Scope decisions (brainstorm)

| Axis | Decision |
|------|----------|
| Acquisition | Manual — user pastes a browser "Copy as cURL" command from a vgmdb request |
| Input format | cURL command only (it carries both `cf_clearance` and `User-Agent` in one paste) |
| Renewal | Manual re-apply: parse a fresh cURL → `set_credentials()` on a live client. No auto-retry callback. |
| Surface | Python API only. No CLI. |
| Validation | Offline parse only. No live network check; a dead-but-well-formed token still surfaces as `CloudflareChallengeError` on first request. |

These reflect the "assist, don't defeat" constraint and the codebase's conservative,
dependency-free style: nothing here adds a runtime dependency.

## Approach (chosen: A — `Credentials` value object)

A small frozen value object is the natural home for the "these two belong together" invariant.
The `(cf_clearance, user_agent)` pair travels as one unit for both *fill* (initial setup) and
*renew* (mid-session swap), and is testable in isolation. Rejected alternatives: B (loose
`(token, ua)` tuple from functions — pair not bound together) and C (methods on
`TransportConfig` taking two args — easy to mis-pair on renewal).

## Module layout

New package `src/vgmdb_client/auth/`:

### `auth/credentials.py`
```python
class Credentials(BaseModel):  # frozen
    cf_clearance: str
    user_agent: str

    @classmethod
    def from_curl(cls, curl_text: str) -> "Credentials": ...
    def to_config(self, **overrides) -> TransportConfig: ...
```
- `from_curl` delegates to the `auth/curl.py` parser, then constructs the pair.
- `to_config(**overrides)` builds a `TransportConfig` with `cf_clearance` + `user_agent` set,
  forwarding any extra `TransportConfig` fields (e.g. `timeout`, `min_interval`, `proxy`).
- Frozen: a credentials object is immutable; renewal means constructing a new one.

### `auth/curl.py`
Clean-room, pure, dependency-free cURL parser.
- `shlex.split(curl_text)` to tokenize (handles the single-quoted form Chrome/Firefox "Copy as
  cURL (bash)" emits).
- Walk tokens, collecting:
  - `-H` / `--header` values: a `Cookie:` header → extract the `cf_clearance=...` value from the
    cookie string (which may hold many cookies); a `User-Agent:` header → the UA.
  - `-b` / `--cookie` value → same cf_clearance extraction.
  - `-A` / `--user-agent` value → the UA.
- Header-name matching is case-insensitive. The last occurrence wins if a field appears twice.
- Returns the `(cf_clearance, user_agent)` strings; raises `CurlParseError` if either is absent.

**Out of scope for the parser (documented, not handled):** Windows "Copy as cURL (cmd)" form
(`^` line-continuation, `"`-quoting) and PowerShell form. The bash single-quote form is the
documented supported paste. (Tracked as a follow-up if users hit it — see Deferred.)

### `auth/errors.py`
```python
class CurlParseError(VgmdbClientError): ...
```
Raised when the paste lacks a `cf_clearance` cookie or a `User-Agent`, or is not parseable.
Message points the user at the correct devtools step ("copy a request to vgmdb.net as cURL,
ensuring it includes the Cookie and User-Agent headers").

## Client integration (fill + renew)

On both `Client` and `AsyncClient`:
- `from_credentials(creds: Credentials, **config_overrides) -> Client` — classmethod for *fill*;
  builds the transport from `creds.to_config(**config_overrides)`.
- `set_credentials(creds: Credentials) -> None` — *renew*; delegates to the transport's existing
  `set_cf_clearance` + `set_user_agent`. (Adds a thin pass-through on the transport's owner; the
  transport seam already exists.)

The existing `Client(config=...)` / `Client(transport=...)` constructors are unchanged.

### Renewal loop (documented pattern)
```python
from vgmdb_client.auth import Credentials
from vgmdb_client.transport.errors import CloudflareChallengeError

client = Client.from_credentials(Credentials.from_curl(curl_text))
try:
    album = client.get_album(4)
except CloudflareChallengeError:
    # token went stale — re-solve in the browser, copy a fresh cURL, re-apply
    client.set_credentials(Credentials.from_curl(fresh_curl))
    album = client.get_album(4)
```

## Public API surface

Exported from `vgmdb_client.auth`: `Credentials`, `CurlParseError`.
`from_credentials` / `set_credentials` live on the existing clients.

## Error handling

- Parse failures → `CurlParseError` (missing token / missing UA / unparseable).
- No network in the helper → no live-validation errors here.
- A dead-but-well-formed token → unchanged behavior: `CloudflareChallengeError` on first request,
  which the renewal loop above handles.

## Testing

Unit tests, no live network:
- **cURL parser** (`auth/curl.py`): Chrome bash-style single-quote paste; Firefox paste;
  `-b`/`-A` short-flag variants; `Cookie:` header with multiple cookies (pick out `cf_clearance`);
  case-insensitive header names; missing-`cf_clearance` → `CurlParseError`; missing-UA →
  `CurlParseError`; unparseable input → `CurlParseError`.
- **`Credentials.from_curl`**: round-trip from a representative paste; `to_config` forwards
  overrides and sets the pair.
- **`set_credentials`**: updates a stub transport's token + UA.
- **`from_credentials`**: builds a client whose transport carries the pair (against a stub).

## Out of scope / deferred

- Auto-refresh callback + retry-on-challenge (considered, rejected for YAGNI; manual re-apply
  chosen).
- CLI entry point.
- Live token validation (`validate()` GET).
- Non-bash cURL paste forms (Windows cmd `^`, PowerShell). **File a follow-up bead** if/when
  needed so the deferral is tracked, per the CLAUDE.md "track every deferral" rule.
- Auto-reading the local browser cookie store / launching an interactive browser (rejected
  acquisition options).
