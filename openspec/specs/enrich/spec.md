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
request to a configured `LLM_URL` and parses the JSON response into an `AlbumEnrichment`. A
`backend_from_env()` helper SHALL return such a backend when `LLM_URL` is set, or `None` otherwise.
Extracted credit role labels SHALL be normalized via `normalize_role` (not taken from the model
output). A configured backend that fails (transport error, non-JSON, or schema-invalid response)
SHALL raise `EnrichmentError`.

#### Scenario: Parses a chat-completion response into enrichment

- **WHEN** the endpoint returns a valid chat-completion whose content is JSON of per-track credits
- **THEN** `OpenAICompatibleBackend.enrich` returns an `AlbumEnrichment` with those credits, each
  credit's `role` set by `normalize_role(role_raw)`

#### Scenario: backend_from_env without LLM_URL

- **WHEN** `backend_from_env()` is called and `LLM_URL` is not set
- **THEN** it returns `None`

#### Scenario: Malformed response raises EnrichmentError

- **WHEN** the endpoint returns a non-JSON or schema-invalid body, or the request fails
- **THEN** `OpenAICompatibleBackend.enrich` raises `EnrichmentError`
