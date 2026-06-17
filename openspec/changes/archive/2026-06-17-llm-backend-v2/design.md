## Context

B1's `OpenAICompatibleBackend` is rigid (fixed prompt, json_object only, loose parse). Full design:
`docs/superpowers/vgmdb_client/2026-06-17_llm_backend_v2_design.md`. Cycle 2 of the Enrichment v2
epic; measured by Cycle 1's scorer.

## Goals / Non-Goals

**Goals:** injectable prompt; selectable `json_object`/`json_schema`/`tool` output; schema-validated
replies + one corrective retry. Backward compatible.

**Non-Goals:** new backends (Cycle 3); changing `AlbumEnrichment`/the protocol; role normalization
stays ours; no live calls in tests.

## Decisions

- **`_LlmResponse` pydantic model** (`track_credits: dict[str, list[{role_raw, artists:[{names}]}]]`)
  is the single source of truth: derives the schema for `json_schema`/`tool` modes and validates the
  reply in all modes. `_build_enrichment` consumes the validated model, applying `normalize_role`.
- **Output modes** via `output_mode`: `json_object` (default — `response_format` json_object);
  `json_schema` (`response_format` json_schema, `strict: false` — `track_credits` is an open-keyed map); `tool` (forced function tool call,
  schema in `parameters`, read from tool-call arguments). Default is `json_object` for compatibility.
- **Prompt**: `system_prompt` + `user_template` ({tracklist}/{notes}) constructor args, defaulting to
  the current text; `_build_messages` renders the template.
- **Validation + retry**: parse → `_LlmResponse.model_validate`; on failure retry up to `max_retries`
  (default 1) with a corrective user message quoting the error; exhaustion → `EnrichmentError`.
  `httpx` errors are not retried (raise immediately).
- **Construction**: `OpenAICompatibleBackend(url, model=..., api_key=None, timeout=30.0, *,
  output_mode="json_object", system_prompt=None, user_template=None, max_retries=1)`.
  `backend_from_env()` reads optional `LLM_OUTPUT_MODE`.

## Risks / Trade-offs

- `json_schema`/`tool` aren't universally supported → default `json_object`, modes are opt-in.
- A corrective retry can double calls → bounded by `max_retries`, skipped when the first reply is
  valid.
- `_LlmResponse` must track what `_build_enrichment` expects → same module; mode tests catch drift.
