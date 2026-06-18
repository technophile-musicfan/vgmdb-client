## Why

`vgmdb.net` is behind Cloudflare: a request only succeeds with a valid `cf_clearance` cookie paired with the exact `User-Agent` it was issued for. The transport can already carry and swap these, but there is no human-facing way to get a fresh pair out of the user's own already-solved browser session and into the client, nor to re-apply one when it expires. This is the V1a feature (epic `vgmdb-0e5.1`) gating the V1 release.

## What Changes

- Add a new `auth` package exposing a frozen `Credentials(cf_clearance, user_agent)` value object that keeps the token and its bound User-Agent together as one unit.
- `Credentials.from_curl(curl_text)` parses a browser "Copy as cURL" paste (bash single-quote form) — `-H` `Cookie:`/`User-Agent:` headers, `-b`/`--cookie`, `-A`/`--user-agent` — extracting both halves in one paste.
- `Credentials.to_config(**overrides)` builds a `TransportConfig` with the pair set, forwarding extra config fields.
- `CurlParseError` (a `VgmdbClientError`) raised when a paste lacks a `cf_clearance` or `User-Agent`, or is unparseable.
- `Client` / `AsyncClient` gain `from_credentials(creds, **overrides)` (initial *fill*) and `set_credentials(creds)` (mid-session *renew*, delegating to the transport's existing `set_cf_clearance` / `set_user_agent`).
- Explicit non-goal: the helper does NOT defeat, solve, or automate the Cloudflare challenge — the human passes it in their browser; the helper only transports the resulting credentials. No live token validation, no CLI, no new runtime dependency.

## Capabilities

### New Capabilities
- `auth`: parsing a browser cURL paste into a validated `(cf_clearance, User-Agent)` credentials pair and building transport config from it; the `CurlParseError` failure mode.

### Modified Capabilities
- `client`: `Client` / `AsyncClient` gain a `from_credentials` constructor and a `set_credentials` method for filling and renewing the credentials pair on a live client.

## Impact

- **New code:** `src/vgmdb_client/auth/` (`credentials.py`, `curl.py`, `errors.py`, `__init__.py`).
- **Modified code:** `client/sync_client.py`, `client/async_client.py` (add `from_credentials` / `set_credentials`).
- **Reused, unchanged:** transport `set_cf_clearance` / `set_user_agent` seam, `TransportConfig`, `CloudflareChallengeError`.
- **Dependencies:** none added (uses stdlib `shlex`).
- **Public API:** `vgmdb_client.auth` exports `Credentials`, `CurlParseError`.
