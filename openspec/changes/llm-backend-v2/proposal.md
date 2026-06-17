## Why

The `OpenAICompatibleBackend` shipped in B1 has a fixed system prompt + hardcoded message builder,
only requests `response_format: json_object`, and validates the reply reactively (a loose
`json.loads` wrapped in try/except). To compare prompts and to get reliably parsable output, the
backend needs a customizable prompt, a way to force structured output, and real schema validation.
This is Cycle 2 of the Enrichment v2 epic (vgmdb-zsy); its quality is measured by Cycle 1's scorer.

## What Changes

- **enrich**: extend `OpenAICompatibleBackend` (no protocol/model change):
  - Injectable `system_prompt` and `user_template` (a format string with `{tracklist}`/`{notes}`);
    the current text becomes the defaults, so existing behavior is unchanged.
  - Selectable `output_mode`: `json_object` (default), `json_schema`, `tool`. `json_schema`/`tool`
    derive their schema from an internal pydantic `_LlmResponse` model.
  - All modes validate the reply via `_LlmResponse.model_validate`; `_build_enrichment` converts the
    validated response into `AlbumEnrichment`, still applying `normalize_role`.
  - One corrective retry on invalid output (`max_retries` default 1, appends a message quoting the
    validation error); exhausted retries raise `EnrichmentError`; transport errors raise immediately.
  - `backend_from_env()` reads optional `LLM_OUTPUT_MODE` (default `json_object`).

## Capabilities

### New Capabilities
<!-- None: extends the existing `enrich` capability. -->

### Modified Capabilities
- `enrich`: prompt customization, selectable structured-output modes, and schema-validated parsing
  with a corrective retry for the OpenAI-compatible backend.

## Impact

- Changes only `src/vgmdb_client/enrich/llm.py` (+ its tests). No change to `AlbumEnrichment`, the
  `EnrichmentBackend` protocol, or other backends.
- No new dependency (httpx/pydantic already present). No runtime behavior change for existing callers
  that pass no new arguments. All tests respx-mocked (no network).
