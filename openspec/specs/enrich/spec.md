# enrich Specification

## Purpose
Opt-in deep-parse enrichment: structured overlays (primarily per-track credits) extracted from an album's freeform vgmdb text without modifying the M1 models. A pluggable backend (an OpenAI-compatible LLM endpoint now, an embedded model later) does the extraction; the package normalizes the result and degrades gracefully when no backend is configured.

## Requirements
### Requirement: Album enrichment overlay

The package SHALL provide an `AlbumEnrichment` model that overlays per-track credits onto an album
without modifying the M1 models: it carries the album id and `track_credits`, a mapping of track
number to a list of `Credit`. It SHALL expose whether it is empty.

#### Scenario: Empty enrichment

- **WHEN** an `AlbumEnrichment` is created with no track credits
- **THEN** `is_empty` is true

#### Scenario: Per-track credits accessible by track number

- **WHEN** an `AlbumEnrichment` carries credits for track 10
- **THEN** those `Credit` entries are retrievable under track number 10 and `is_empty` is false

### Requirement: Pluggable enrichment backend

The package SHALL define an `EnrichmentBackend` protocol with `enrich(album, raw_text) ->
AlbumEnrichment`, so different backends (an LLM endpoint now, an embedded model later) are
interchangeable.

#### Scenario: A custom backend conforms

- **WHEN** an object implementing `enrich(album, raw_text) -> AlbumEnrichment` is supplied to the
  helper
- **THEN** its returned enrichment is used

### Requirement: Deep-parse helper

The package SHALL provide `enrich_album(album, backend=None) -> AlbumEnrichment`. With no backend it
SHALL return an empty `AlbumEnrichment` (graceful degradation, no error); with a backend it SHALL
return that backend's enrichment for the album using the album's raw notes as the freeform text.

#### Scenario: No backend degrades to empty

- **WHEN** `enrich_album(album)` is called with no backend configured
- **THEN** it returns an empty `AlbumEnrichment` and raises no error

#### Scenario: Backend enrichment returned

- **WHEN** `enrich_album(album, backend)` is called with a backend
- **THEN** it returns the `AlbumEnrichment` produced by that backend

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

### Requirement: Rule-based enrichment backend

The package SHALL provide a deterministic `RuleBasedBackend` implementing the `EnrichmentBackend`
protocol (`enrich(album, raw_text) -> AlbumEnrichment`) with no additional dependency. It SHALL
extract per-track credits from the album's freeform notes by parsing track-range notations
(comma lists, `~` ranges, `M`/`M-`/leading-zero prefixes), an inline-parenthetical pattern
(`<Name> (<ranges>)` under a role context), and a block pattern (a track-range/number header line
sets the current track set and subsequent role lines attribute to it). Extracted role labels SHALL be
normalized via `normalize_role`.

A role line SHALL emit credits only when it has a track context (a preceding range/number header) or
an inline range; credits with no track reference (album-level) SHALL be dropped. The backend SHALL be
deterministic and SHALL NOT perform any network access.

#### Scenario: Block pattern attributes a role line to a preceding range header

- **WHEN** notes contain a track-range header followed by a `<Role> by <Names>` line
- **THEN** the named artists are credited (with the normalized role) to every track in that range

#### Scenario: Inline parenthetical attributes names to their ranges

- **WHEN** notes contain `<Role>: <Name> (<ranges>)` groups
- **THEN** each name is credited to the tracks in its parenthetical range

#### Scenario: Album-level credit without a track reference is dropped

- **WHEN** notes contain a role/credit line with no track range or number context
- **THEN** no credit is emitted for it (the enrichment stays empty for that content)

#### Scenario: Track-range notations are parsed

- **WHEN** a range is written as a comma list, a `~` range, or with `M`/`M-`/leading-zero prefixes
- **THEN** it resolves to the corresponding set of track numbers
