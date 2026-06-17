## 1. Response model + validation

- [ ] 1.1 `src/vgmdb_client/enrich/llm.py`: add internal `_LlmResponse` pydantic model
  (`track_credits: dict[str, list[_LlmCredit]]`, `_LlmCredit{role_raw, artists:[_LlmArtist{names}]}`).
- [ ] 1.2 Rework `_build_enrichment` to consume a validated `_LlmResponse` (still applying
  `normalize_role`); validation failures raise `EnrichmentError`.

## 2. Prompt customization

- [ ] 2.1 Constructor gains `system_prompt: str | None` + `user_template: str | None` (defaults =
  current text). `_build_messages` renders `user_template` with `{tracklist}`/`{notes}`.
- [ ] 2.2 Test: custom prompt/template appear in the request; defaults reproduce current B1 messages.

## 3. Output modes

- [ ] 3.1 Add `output_mode: "json_object" | "json_schema" | "tool"` (default `json_object`). Build the
  request per mode: json_object response_format; json_schema response_format with derived schema +
  `strict: true`; tool with a forced function tool call carrying the schema.
- [ ] 3.2 Parse per mode (content for object/schema; tool-call arguments for tool) → validate via
  `_LlmResponse`. Tests (respx): each mode's request shape + a valid reply parsed to `AlbumEnrichment`.

## 4. Retry + env + gate

- [ ] 4.1 Validation/parse failure retries up to `max_retries` (default 1) with a corrective message
  quoting the error; exhausted → `EnrichmentError`; transport errors raise immediately. Tests:
  invalid-then-valid recovers; invalid-twice (and `max_retries=0`) → `EnrichmentError`.
- [ ] 4.2 `backend_from_env()` reads optional `LLM_OUTPUT_MODE` (default `json_object`); test set/unset.
- [ ] 4.3 Full gate (ruff + mypy + pytest) green; existing B1 enrich tests still pass unchanged.
