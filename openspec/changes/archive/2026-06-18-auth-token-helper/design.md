## Context

`vgmdb.net` is behind Cloudflare; a request succeeds only with a valid `cf_clearance` cookie paired
with the exact `User-Agent` it was issued for (the token is bound to that UA and the client IP). The
transport (`vgmdb-v9g.4`) already injects both, exposes `set_cf_clearance` / `set_user_agent`, and
raises a non-retried `CloudflareChallengeError` on a missing/stale token. The gap is human-facing:
getting a fresh pair out of the user's own already-solved browser session into the client, and
re-applying one when it expires. Full brainstorm:
`docs/superpowers/vgmdb_client/2026-06-18_auth_token_helper_design.md`.

## Goals / Non-Goals

**Goals:**
- One-paste acquisition of the `(cf_clearance, User-Agent)` pair from a browser "Copy as cURL".
- Keep the pair together as one immutable unit usable for both initial fill and mid-session renew.
- Zero new runtime dependencies; no network I/O in the helper.

**Non-Goals:**
- Defeating / solving / automating the Cloudflare challenge (the human does this in their browser).
- Live token validation, a CLI, auto-refresh callbacks, browser-cookie reading, non-bash cURL forms.

## Decisions

- **`Credentials` value object (vs. loose functions / `TransportConfig` methods).** A frozen pair is
  the natural home for the "token and UA belong together" invariant and is reusable for fill and
  renew; a loose `(token, ua)` tuple or two-arg config methods make mis-pairing on renewal easy.
- **cURL as the sole input.** A single "Copy as cURL" paste carries both halves, so the user never
  hand-pairs token and UA. Parser uses stdlib `shlex.split` (handles the bash single-quote form),
  then walks tokens for `-H`/`--header` (`Cookie:`/`User-Agent:`), `-b`/`--cookie`, `-A`/
  `--user-agent`; case-insensitive header names; last occurrence wins.
- **Manual re-apply renewal (vs. auto-refresh callback).** `set_credentials` delegates to the
  transport's existing setter seam; the caller re-pastes a fresh cURL on `CloudflareChallengeError`.
  No callback is wired into the retry path, avoiding prompt-loop and re-entrancy complexity.
- **Offline parse only.** A dead-but-well-formed token still surfaces as the existing
  `CloudflareChallengeError` on first request, so a live `validate()` adds little for the cost.

## Risks / Trade-offs

- **Non-bash cURL pastes (Windows cmd `^`, PowerShell) won't parse.** → Documented as the supported
  form is the bash single-quote paste; a follow-up bead is filed if users hit it.
- **A stale token is only detected on first real request, not at parse time.** → Accepted; the
  renewal loop (`except CloudflareChallengeError: set_credentials(...)`) is the documented pattern.
- **cURL formats drift across browsers.** → Parser keys off cURL flags, not browser specifics, and is
  covered by Chrome/Firefox/short-flag fixture tests.
