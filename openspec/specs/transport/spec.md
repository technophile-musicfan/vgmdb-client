# transport Specification

## Purpose
TBD - created by archiving change transport-layer. Update Purpose after archive.
## Requirements
### Requirement: Authenticated page fetch

The transport SHALL fetch a vgmdb page given a path and return the response body as raw HTML
text (`str`), joining the path against the configured `base_url`. It SHALL send the configured
`cf_clearance` value as a `cf_clearance` cookie and the configured `User-Agent` on every request.

#### Scenario: Successful fetch returns HTML

- **WHEN** `get(path)` is called and vgmdb responds `200` with an HTML body
- **THEN** the transport returns the decoded body as a `str`

#### Scenario: Credentials are attached to the request

- **WHEN** `get(path)` is called on a transport configured with a `cf_clearance` and `User-Agent`
- **THEN** the outgoing request carries the `cf_clearance` cookie and the configured `User-Agent` header

### Requirement: Synchronous and asynchronous clients

The transport SHALL provide both a synchronous client and an asynchronous client exposing the
same surface (`get`, `set_cf_clearance`, `set_user_agent`, close). Both SHALL share a single
sans-I/O core for request assembly, response classification, retry policy, and throttle timing,
so that no classification or policy logic is duplicated between them.

#### Scenario: Sync client fetches a page

- **WHEN** a `SyncTransport` calls `get(path)` against a `200` response
- **THEN** it returns the HTML body synchronously

#### Scenario: Async client fetches a page

- **WHEN** an `AsyncTransport` awaits `get(path)` against a `200` response
- **THEN** it returns the HTML body

#### Scenario: Both clients classify responses identically

- **WHEN** the same response is processed by the sync and the async client
- **THEN** both produce the same result or raise the same error type

### Requirement: Cloudflare challenge detection

The transport SHALL detect a Cloudflare challenge and raise `CloudflareChallengeError`,
distinguishing it from a genuine not-found response. A response with status `403` or `503` that
carries Cloudflare challenge markers (a `cf-mitigated: challenge` header, or a recognized
challenge body signature corroborated by Cloudflare response headers) SHALL be treated as a
challenge.

#### Scenario: Challenge header detected

- **WHEN** a response returns `403` with a `cf-mitigated: challenge` header
- **THEN** the transport raises `CloudflareChallengeError`

#### Scenario: Challenge body detected

- **WHEN** a response returns `503` whose body contains a Cloudflare challenge signature alongside Cloudflare response headers
- **THEN** the transport raises `CloudflareChallengeError`

#### Scenario: Challenge error guides token refresh

- **WHEN** a `CloudflareChallengeError` is raised
- **THEN** its message indicates that the `cf_clearance` token must be supplied or refreshed

### Requirement: Not-found classification

The transport SHALL raise `NotFoundError` for an application-level `404` response, and SHALL NOT
classify it as a Cloudflare challenge.

#### Scenario: 404 raises NotFoundError

- **WHEN** vgmdb responds `404`
- **THEN** the transport raises `NotFoundError` and not `CloudflareChallengeError`

### Requirement: Rate-limit classification

The transport SHALL raise `RateLimitedError` for a `429` response and expose the `Retry-After`
value when present. It SHALL NOT automatically retry a rate-limited response.

#### Scenario: 429 raises RateLimitedError with retry-after

- **WHEN** vgmdb responds `429` with a `Retry-After` header
- **THEN** the transport raises `RateLimitedError` exposing the parsed `retry_after`, without retrying

### Requirement: Retry of transient failures only

The transport SHALL retry transient failures (connection errors, timeouts, and `5xx` responses
other than a recognized Cloudflare challenge) using exponential backoff with jitter, bounded by
the configured maximum attempts. It SHALL NOT retry a Cloudflare challenge, a `404`, or a `429`.
When retries are exhausted, it SHALL raise `TransientTransportError`.

#### Scenario: Transient failure is retried then succeeds

- **WHEN** the first attempt fails with a timeout and a subsequent attempt returns `200`
- **THEN** the transport retries and returns the HTML body

#### Scenario: Retries are exhausted

- **WHEN** every attempt fails transiently up to the configured maximum
- **THEN** the transport raises `TransientTransportError`

#### Scenario: Non-transient errors are not retried

- **WHEN** a response is classified as a Cloudflare challenge, `404`, or `429`
- **THEN** the transport raises the corresponding error immediately without retrying

### Requirement: Politeness throttle

The transport SHALL enforce a configurable minimum interval between request starts in both the
sync and async clients. A configured interval of `0` SHALL disable throttling.

#### Scenario: Minimum interval enforced between requests

- **WHEN** two requests are issued in succession with a positive `min_interval`
- **THEN** the second request does not start until at least `min_interval` has elapsed since the first

#### Scenario: Throttle disabled

- **WHEN** `min_interval` is `0`
- **THEN** requests are issued without an enforced delay

### Requirement: Live credential refresh

The transport SHALL allow updating the `cf_clearance` token and the `User-Agent` on an existing
client without reconstructing it, and subsequent requests SHALL use the updated values.

#### Scenario: Token refreshed mid-session

- **WHEN** `set_cf_clearance(new_token)` is called on a live transport
- **THEN** subsequent requests send the new `cf_clearance` cookie value

#### Scenario: User-Agent refreshed mid-session

- **WHEN** `set_user_agent(new_ua)` is called on a live transport
- **THEN** subsequent requests send the new `User-Agent` header

### Requirement: Typed error hierarchy

The transport errors SHALL derive from a transport base error which derives from a library-wide
base error, so that callers can catch transport failures broadly or by specific type.

#### Scenario: Specific errors share a common base

- **WHEN** a `CloudflareChallengeError`, `NotFoundError`, `RateLimitedError`, or `TransientTransportError` is raised
- **THEN** it can be caught as the transport base error and as the library-wide base error

