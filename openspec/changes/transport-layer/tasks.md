## 1. Dependencies & scaffolding

- [x] 1.1 Add runtime deps `httpx`, `tenacity`, `pydantic` and dev dep `respx` to `pyproject.toml`; sync the lockfile
- [x] 1.2 Create the `src/vgmdb_client/transport/` package and an empty `tests/unit_tests/transport/` test package
- [x] 1.3 Add `src/vgmdb_client/errors.py` with the library-wide base `VgmdbClientError`

## 2. Errors & config

- [x] 2.1 Add `transport/errors.py`: `TransportError(VgmdbClientError)` and subclasses `CloudflareChallengeError`, `NotFoundError`, `RateLimitedError` (with `retry_after`), `TransientTransportError`
- [x] 2.2 Test the error hierarchy: each specific error is catchable as `TransportError` and as `VgmdbClientError`
- [x] 2.3 Add `transport/config.py`: pydantic v2 `TransportConfig` (base_url, user_agent, cf_clearance, timeout, max_retries, backoff_base, backoff_max, min_interval, proxy) with defaults from the design

## 3. Sans-I/O core

- [x] 3.1 Implement `classify_response(status, headers, text)` in `transport/core.py` per the detection order (404 → CF challenge → 429 → transient → OK)
- [x] 3.2 Unit-test `classify_response` truth table: 200 OK, 404, 403+`cf-mitigated`, 503+body signature, 429 (+retry_after), generic 5xx
- [x] 3.3 Implement request assembly (URL join against base_url, header/cookie construction) as pure helpers — header/cookie assembly in `core.py` (`build_headers`/`build_cookies`); URL joining delegated to httpx `base_url`
- [x] 3.4 Implement the tenacity retry policy/predicate (retry only `TransientTransportError`; exponential backoff + jitter bounded by max_retries/backoff_max) and the throttle wait-time calculation
- [x] 3.5 Unit-test the throttle wait-time calculation (monkeypatched clock): positive interval enforced, `0` disables

## 4. Sync client

- [ ] 4.1 Implement `SyncTransport` over `httpx.Client`: `get(path)`, `set_cf_clearance`, `set_user_agent`, `close`, context manager; apply throttle + retry + `classify_response`
- [ ] 4.2 Tests (httpx.MockTransport/respx): 200 returns HTML; cf_clearance cookie + User-Agent attached; 404→NotFoundError; CF→CloudflareChallengeError; 429→RateLimitedError (not retried); transient retried then succeeds; retries exhausted→TransientTransportError; CF/404 not retried
- [ ] 4.3 Tests: `set_cf_clearance`/`set_user_agent` update values used by subsequent requests; min_interval enforced between two requests

## 5. Async client

- [ ] 5.1 Implement `AsyncTransport` over `httpx.AsyncClient`: async `get`/`aclose`, async context manager, `set_*`; reuse the shared core (throttle via `asyncio.sleep`)
- [ ] 5.2 Async tests mirroring 4.2/4.3 (challenge/404/429/transient/throttle/refresh)
- [ ] 5.3 Parity test: the same response yields the same result or error type across sync and async

## 6. Packaging & wiring

- [ ] 6.1 Export `SyncTransport`, `AsyncTransport`, `TransportConfig`, and the error types from `transport/__init__.py`
- [ ] 6.2 Run ruff, mypy, and the full test suite; fix issues until green
