## MODIFIED Requirements

### Requirement: OpenAI-compatible LLM backend

The package SHALL provide an `OpenAICompatibleBackend` that POSTs an OpenAI-compatible chat-completion
request to a configured `LLM_URL` and returns an `AlbumEnrichment`. A `backend_from_env()` helper
SHALL return such a backend when `LLM_URL` is set, or `None` otherwise. Extracted credit role labels
SHALL be normalized via `normalize_role` (not taken from the model output).

The backend SHALL support a selectable `output_mode`: `json_object` (the default), `json_schema`, and
`tool`. In `json_schema` and `tool` modes the request SHALL carry a schema derived from an internal
response model; in `tool` mode the result SHALL be read from the forced tool call's arguments. In all
modes the reply SHALL be validated against that response model before being converted to an
`AlbumEnrichment`.

The backend SHALL accept a customizable system prompt and user-message template (with `{tracklist}`
and `{notes}` placeholders); when not provided it SHALL use built-in defaults so existing behavior is
unchanged. `backend_from_env()` SHALL read an optional `LLM_OUTPUT_MODE` (default `json_object`).

On an invalid (unparsable or schema-invalid) reply the backend SHALL retry up to `max_retries` times
(default 1), appending a corrective message that states the validation error; once retries are
exhausted, or on a transport error, it SHALL raise `EnrichmentError`.

#### Scenario: Default mode parses a chat-completion response

- **WHEN** the endpoint returns a valid chat-completion whose content is JSON of per-track credits
- **THEN** the backend returns an `AlbumEnrichment` with those credits, each credit's `role` set by
  `normalize_role(role_raw)`

#### Scenario: json_schema mode sends a schema and parses the reply

- **WHEN** the backend is in `json_schema` mode
- **THEN** the request carries the derived response schema and a valid reply is parsed into an
  `AlbumEnrichment`

#### Scenario: tool mode reads the forced tool call

- **WHEN** the backend is in `tool` mode
- **THEN** the request forces a tool call carrying the derived schema and the result is read from the
  tool call's arguments into an `AlbumEnrichment`

#### Scenario: Custom prompt is used

- **WHEN** a custom system prompt and user template are supplied
- **THEN** the outgoing request reflects them (and defaults are used when they are not supplied)

#### Scenario: Corrective retry recovers from an invalid reply

- **WHEN** the first reply is schema-invalid and a retry is allowed
- **THEN** the backend retries with a corrective message and returns the enrichment from the valid
  retry

#### Scenario: Exhausted retries raise EnrichmentError

- **WHEN** every allowed attempt returns an invalid reply, or the request fails at the transport layer
- **THEN** the backend raises `EnrichmentError`

#### Scenario: backend_from_env without LLM_URL

- **WHEN** `backend_from_env()` is called and `LLM_URL` is not set
- **THEN** it returns `None`
