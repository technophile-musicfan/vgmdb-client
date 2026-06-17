# LLM Backend v2 (Enrichment v2, Cycle 2) — Design

**Bead:** vgmdb-zsy.2 · **Date:** 2026-06-17 · **Workflow:** 2.

## Why

`OpenAICompatibleBackend` ships with a **fixed** system prompt + hardcoded message builder, uses
`response_format: json_object` + manual `json.loads`, and validates only reactively (catch → error).
This cycle makes the prompt customizable, lets callers **force structured output**, and replaces the
loose parse with schema validation + a corrective retry. It consumes Cycle 1's scorer to quantify the
effect. No change to `AlbumEnrichment`, the `EnrichmentBackend` protocol, or the lightweight backends
(Cycle 3).

## Goals / Non-Goals

**Goals:**
- Injectable system prompt + user-message template (current text = defaults; backward compatible).
- Selectable output modes: `json_object` (default), `json_schema`, `tool`.
- Schema-validated responses (a pydantic response model) + one corrective retry on invalid output.

**Non-Goals:**
- New backends (Cycle 3). No live LLM calls in tests (respx-mocked).
- Changing how roles are normalized (still our `normalize_role`, not the model's).

## Decisions

### Response schema (validation backbone)

Internal pydantic model mirroring the expected LLM JSON, the single source of truth for both schema
derivation and validation:

```python
class _LlmArtist(BaseModel):   names: dict[str, str]
class _LlmCredit(BaseModel):   role_raw: str; artists: list[_LlmArtist] = []
class _LlmResponse(BaseModel): track_credits: dict[str, list[_LlmCredit]] = {}
```

Every mode validates its reply via `_LlmResponse.model_validate(...)`; `json_schema` / `tool` modes
derive their schema from `_LlmResponse.model_json_schema()`. `_build_enrichment` converts the
**validated** `_LlmResponse` into `AlbumEnrichment`, applying `normalize_role` to each `role_raw`
(unchanged behavior, now fed validated data).

### Output modes (`output_mode`)

- **`json_object`** (default) — `response_format={"type": "json_object"}`; parse `message.content`.
- **`json_schema`** — `response_format={"type": "json_schema", "json_schema": {"name": ...,
  "schema": <derived>, "strict": false}}`; parse `message.content`. (strict is false because
  `track_credits` is an open-keyed map, which OpenAI strict mode cannot express.)
- **`tool`** — `tools=[{"type": "function", "function": {"name": ..., "parameters": <derived>}}]`
  with forced `tool_choice`; parse the tool call's `arguments`.

Default is `json_object` for maximal compatibility (many local/self-hosted endpoints lack
structured-output support); callers opt into `json_schema` / `tool`.

### Prompt customization

Constructor gains `system_prompt: str | None` and `user_template: str | None`. `user_template` is a
format string with `{tracklist}` and `{notes}` placeholders. Both default to the current text, so
existing behavior is unchanged. `_build_messages` renders the template.

### Validation + retry

Parse the reply, then `_LlmResponse.model_validate`. On parse/validation failure, retry up to
`max_retries` (default 1), appending a corrective user message that quotes the error and re-states
the schema requirement (so the retry differs even at temperature 0). Exhausted retries raise
`EnrichmentError` (as today). Transport (`httpx`) errors are not retried by this loop — they raise
`EnrichmentError` immediately, as now.

### Construction

`OpenAICompatibleBackend(url, model=..., api_key=None, timeout=30.0, *, output_mode="json_object",
system_prompt=None, user_template=None, max_retries=1)`. `backend_from_env()` additionally reads an
optional `LLM_OUTPUT_MODE` (default `json_object`); prompt/template stay code-configured (env is for
deployment switches, not long text).

## Testing (all respx-mocked, no network)

- Each mode's outgoing request shape: `json_object` sets the json_object response_format; `json_schema`
  includes the derived schema (strict: false — open-keyed map); `tool` forces a tool call and the schema rides in
  `parameters`.
- Each mode parses a valid reply (content for object/schema; tool-call arguments for tool) into the
  expected `AlbumEnrichment` with `normalize_role` applied.
- Invalid-then-valid: first reply fails validation, retry (with corrective message) succeeds.
- Invalid twice (or `max_retries=0`) → `EnrichmentError`.
- Custom `system_prompt` / `user_template` appear in the request; defaults reproduce current B1
  behavior (existing B1 tests stay green).
- `backend_from_env` honors `LLM_OUTPUT_MODE`.

## Risks / Trade-offs

- **Endpoint capability variance.** `json_schema` / `tool` aren't universally supported; mitigated by
  defaulting to `json_object` and making the mode explicit/opt-in.
- **Retry cost.** A corrective retry doubles calls in the worst case; bounded by `max_retries`
  (default 1) and skipped entirely when the first reply validates.
- **Schema drift.** `_LlmResponse` must track the shape `_build_enrichment` expects; they live in the
  same module and a mismatch fails the mode tests.
