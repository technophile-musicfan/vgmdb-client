## ADDED Requirements

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
