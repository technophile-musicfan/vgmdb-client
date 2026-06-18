# auth Specification

## Purpose
TBD - created by archiving change auth-token-helper. Update Purpose after archive.
## Requirements
### Requirement: Credentials pair

The package SHALL provide an immutable `Credentials` value object holding a `cf_clearance` token and
the `user_agent` it is bound to, keeping the two together as a single unit. Constructing a
`Credentials` SHALL require both fields to be non-empty.

#### Scenario: credentials hold both halves

- **WHEN** a `Credentials` is constructed with a `cf_clearance` and a `user_agent`
- **THEN** both values are accessible on the object and the object is immutable (frozen)

#### Scenario: empty field rejected

- **WHEN** a `Credentials` is constructed with an empty `cf_clearance` or an empty `user_agent`
- **THEN** construction raises a validation error

### Requirement: Parse credentials from a cURL paste

`Credentials` SHALL provide `from_curl(curl_text)` that parses a browser "Copy as cURL" command
(bash single-quote form) and returns a `Credentials` carrying the `cf_clearance` and `User-Agent`
found in it. It SHALL read the token from a `-H 'Cookie: ...'` header or a `-b`/`--cookie` value
(selecting the `cf_clearance` entry from a multi-cookie string), and the User-Agent from a
`-H 'User-Agent: ...'` header or an `-A`/`--user-agent` value. Header-name matching SHALL be
case-insensitive; when a field appears more than once the last occurrence SHALL win.

#### Scenario: extracts both halves from a Chrome cURL paste

- **WHEN** `Credentials.from_curl` is given a bash-style cURL command whose `Cookie:` header
  contains `cf_clearance=<token>` and which has a `User-Agent:` header
- **THEN** it returns a `Credentials` with that token and that user agent

#### Scenario: selects cf_clearance from a multi-cookie header

- **WHEN** the `Cookie:` header contains several cookies including `cf_clearance=<token>`
- **THEN** only the `cf_clearance` value is taken as the token

#### Scenario: reads short-flag forms

- **WHEN** the command supplies the cookie via `-b`/`--cookie` and the agent via `-A`/`--user-agent`
- **THEN** both are extracted

### Requirement: cURL parse failures are typed

`from_curl` SHALL raise `CurlParseError` (a `VgmdbClientError`) when the paste lacks a `cf_clearance`
value, lacks a `User-Agent`, or cannot be tokenized as a command. The error message SHALL point the
user at copying a vgmdb request as cURL with the Cookie and User-Agent headers included.

#### Scenario: missing cf_clearance

- **WHEN** `from_curl` is given a command with a `User-Agent` but no `cf_clearance` cookie
- **THEN** it raises `CurlParseError`

#### Scenario: missing User-Agent

- **WHEN** `from_curl` is given a command with a `cf_clearance` cookie but no `User-Agent`
- **THEN** it raises `CurlParseError`

#### Scenario: unparseable input

- **WHEN** `from_curl` is given text that cannot be tokenized as a shell command
- **THEN** it raises `CurlParseError`

### Requirement: Build transport config from credentials

`Credentials` SHALL provide `to_config(**overrides)` that returns a `TransportConfig` with
`cf_clearance` and `user_agent` set from the pair, forwarding any additional `TransportConfig` fields
passed as keyword overrides (e.g. `timeout`, `min_interval`, `proxy`).

#### Scenario: config carries the pair

- **WHEN** `to_config()` is called on a `Credentials`
- **THEN** the returned `TransportConfig` has the same `cf_clearance` and `user_agent`

#### Scenario: overrides are forwarded

- **WHEN** `to_config(min_interval=0)` is called
- **THEN** the returned `TransportConfig` has `min_interval == 0` and still carries the pair

### Requirement: Auth public API surface

The `vgmdb_client.auth` package SHALL export `Credentials` and `CurlParseError`. The helper SHALL add
no runtime dependency (the cURL parser uses only the standard library) and SHALL perform no network
I/O — it does not validate the token against vgmdb and does not solve the Cloudflare challenge.

#### Scenario: auth imports

- **WHEN** a consumer does `from vgmdb_client.auth import Credentials, CurlParseError`
- **THEN** the import succeeds

