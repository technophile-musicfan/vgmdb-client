# client Specification

## Purpose
The public API: a synchronous Client and an asynchronous AsyncClient that compose the transport and parsers over a shared core, exposing get_album(id) -> Album and search(query) -> SearchResults that return validated M1 models. Config-object construction with transport injection, context-manager lifecycle, and pass-through errors.
## Requirements
### Requirement: Synchronous client

The package SHALL provide a `Client` that fetches and parses vgmdb pages into M1 models:
`get_album(album_id: int) -> Album` and `search(query: str) -> SearchResults`. It SHALL accept a
`TransportConfig` (constructing a `SyncTransport`) or an injected transport, and SHALL be usable as a
context manager that closes the transport on exit.

#### Scenario: get_album returns the parsed album

- **WHEN** `Client.get_album(id)` is called and the transport returns that album's HTML
- **THEN** it returns the `Album` parsed from that HTML

#### Scenario: search returns the parsed results

- **WHEN** `Client.search(query)` is called and the transport returns the search HTML
- **THEN** it returns the `SearchResults` parsed from that HTML

#### Scenario: context manager closes the transport

- **WHEN** a `Client` is used as a context manager and the block exits
- **THEN** the underlying transport is closed

#### Scenario: construction requires exactly one source

- **WHEN** a `Client` is constructed with neither a config nor a transport (or with both)
- **THEN** it raises `ValueError`

### Requirement: Asynchronous client

The package SHALL provide an `AsyncClient` with `async get_album(album_id) -> Album` and
`async search(query) -> SearchResults`, sharing the album/search path logic and parsers with `Client`
(no duplicated parsing or path logic). It SHALL accept a `TransportConfig` (constructing an
`AsyncTransport`) or an injected async transport, and SHALL be usable as an async context manager that
closes the transport on exit.

#### Scenario: async get_album returns the parsed album

- **WHEN** `await AsyncClient.get_album(id)` is called and the transport returns that album's HTML
- **THEN** it returns the `Album` parsed from that HTML

#### Scenario: sync and async agree

- **WHEN** `Client` and `AsyncClient` are given the same page HTML for the same request
- **THEN** they return equal models

#### Scenario: async context manager closes the transport

- **WHEN** an `AsyncClient` is used as an async context manager and the block exits
- **THEN** the underlying transport is closed via `aclose`

### Requirement: Request path construction

The client SHALL build request paths from a shared core: an album request uses `"/album/{id}"` and a
search request uses `"/search?q=<url-encoded query>"`.

#### Scenario: album path

- **WHEN** the album path is built for id 271
- **THEN** it is `"/album/271"`

#### Scenario: search path encodes the query

- **WHEN** the search path is built for the query "final fantasy"
- **THEN** the query is URL-encoded (spaces become `+`)

### Requirement: Error propagation

The client SHALL NOT add error semantics: the transport's typed errors and the parser's `ParseError`
SHALL propagate unchanged from `get_album` and `search`.

#### Scenario: transport error propagates

- **WHEN** the transport raises `NotFoundError` for a missing album
- **THEN** `get_album` propagates `NotFoundError`

#### Scenario: parse error propagates

- **WHEN** the fetched HTML is not a recognizable album page
- **THEN** `get_album` propagates `ParseError`

### Requirement: Public API surface

The top-level `vgmdb_client` package SHALL re-export the public API: `Client`, `AsyncClient`,
`TransportConfig`, the M1 models (and `Role`/`normalize_role`), and the error hierarchy
(`VgmdbClientError`, `ParseError`, and the transport errors).

#### Scenario: top-level imports

- **WHEN** a consumer does `from vgmdb_client import Client, Album, NotFoundError`
- **THEN** the import succeeds

### Requirement: Fetch an artist

`Client` and `AsyncClient` SHALL each provide `get_artist(artist_id)` that fetches the artist page
(path `/artist/{id}`) and returns a parsed `Artist`, reusing the shared transport and error
pass-through.

#### Scenario: get_artist returns the parsed artist

- **WHEN** `get_artist(id)` is called
- **THEN** it fetches `/artist/{id}` via the transport and returns the parsed `Artist`

### Requirement: Fetch a product

`Client` and `AsyncClient` SHALL each provide `get_product(product_id)` that fetches the product page
(path `/product/{id}`) and returns a parsed `Product`.

#### Scenario: get_product returns the parsed product

- **WHEN** `get_product(id)` is called
- **THEN** it fetches `/product/{id}` via the transport and returns the parsed `Product`

### Requirement: Fetch an organization

`Client` and `AsyncClient` SHALL each provide `get_organization(org_id)` that fetches the
organization page (path `/org/{id}`) and returns a parsed `Organization`.

#### Scenario: get_organization returns the parsed organization

- **WHEN** `get_organization(id)` is called
- **THEN** it fetches `/org/{id}` via the transport and returns the parsed `Organization`

### Requirement: Build a client from credentials

`Client` and `AsyncClient` SHALL each provide a `from_credentials(creds, **config_overrides)`
classmethod that builds the client from a `Credentials` pair, constructing the transport from
`creds.to_config(**config_overrides)`. The existing config/transport constructors SHALL remain
unchanged.

#### Scenario: from_credentials builds a working client

- **WHEN** `Client.from_credentials(creds)` is called with a `Credentials` pair
- **THEN** the resulting client's transport carries that `cf_clearance` and `user_agent`

#### Scenario: config overrides are forwarded

- **WHEN** `Client.from_credentials(creds, min_interval=0)` is called
- **THEN** the client's transport config has `min_interval == 0` and still carries the pair

### Requirement: Renew credentials on a live client

`Client` and `AsyncClient` SHALL each provide `set_credentials(creds)` that applies a fresh
`Credentials` pair to the live client by delegating to the transport's `set_cf_clearance` and
`set_user_agent`, so a stale token can be replaced mid-session without rebuilding the client.

#### Scenario: set_credentials swaps the pair

- **WHEN** `set_credentials(creds)` is called on a client whose transport had a different pair
- **THEN** subsequent requests use the new `cf_clearance` and `user_agent`

#### Scenario: renewal after a Cloudflare challenge

- **WHEN** a request raises `CloudflareChallengeError` and the caller then calls `set_credentials`
  with a freshly parsed `Credentials` and retries
- **THEN** the retry uses the new pair

