## 1. Auth package scaffold

- [ ] 1.1 Create `src/vgmdb_client/auth/` package with `__init__.py` exporting `Credentials` and `CurlParseError`
- [ ] 1.2 Add `auth/errors.py` with `CurlParseError(VgmdbClientError)` and a message pointing at the "Copy as cURL with Cookie + User-Agent" step

## 2. cURL parser

- [ ] 2.1 Add `auth/curl.py` `parse_curl(curl_text) -> tuple[str, str]`: `shlex.split` then walk tokens for `-H`/`--header` (`Cookie:` → pick out `cf_clearance`; `User-Agent:`), `-b`/`--cookie`, `-A`/`--user-agent`; case-insensitive header names; last occurrence wins
- [ ] 2.2 Raise `CurlParseError` on missing `cf_clearance`, missing `User-Agent`, or untokenizable input
- [ ] 2.3 Unit tests: Chrome bash paste, Firefox paste, `-b`/`-A` short flags, multi-cookie `Cookie:` header, case-insensitive headers, missing-token, missing-UA, unparseable input

## 3. Credentials value object

- [ ] 3.1 Add `auth/credentials.py` frozen `Credentials(cf_clearance, user_agent)` rejecting empty fields
- [ ] 3.2 `Credentials.from_curl(curl_text)` delegating to `parse_curl`
- [ ] 3.3 `Credentials.to_config(**overrides) -> TransportConfig` setting the pair and forwarding overrides
- [ ] 3.4 Unit tests: `from_curl` round-trip, `to_config` carries pair + forwards overrides, empty-field rejection, frozen/immutable

## 4. Client integration (fill + renew)

- [ ] 4.1 Add `Client.from_credentials(creds, **config_overrides)` and `Client.set_credentials(creds)` (delegating to transport `set_cf_clearance` / `set_user_agent`)
- [ ] 4.2 Add the same `from_credentials` / `set_credentials` to `AsyncClient`
- [ ] 4.3 Unit tests against a stub transport: `from_credentials` builds a client carrying the pair (forwards overrides); `set_credentials` swaps the pair; sync + async parity

## 5. Wiring, docs, and verification

- [ ] 5.1 Confirm public surface: `from vgmdb_client.auth import Credentials, CurlParseError` works; decide/document any top-level re-export
- [ ] 5.2 Document the renewal loop (`except CloudflareChallengeError: set_credentials(Credentials.from_curl(fresh_curl))`) in module docstring / docs
- [ ] 5.3 Run ruff + mypy + full test suite green; confirm no new runtime dependency added
- [ ] 5.4 File a follow-up bead for non-bash cURL paste forms (Windows cmd `^`, PowerShell), per the "track every deferral" rule
