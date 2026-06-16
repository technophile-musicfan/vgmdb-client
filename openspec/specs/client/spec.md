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
