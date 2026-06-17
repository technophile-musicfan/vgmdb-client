## Why

We ship a clean-room parser (M3) and an opt-in LLM deep-parse overlay (B1), but we have no objective
measure of how well either extracts vgmdb album data. Without measurement we cannot rank parser
choices, justify the LLM overlay, or catch regressions in extraction quality. We have a hand-authored
golden dataset (M5) that can serve as ground truth, and a mature third-party parser
(hufman/vgmdb, the vgmdb.info service) we can benchmark against.

## What Changes

- Add a dev-only quality harness under `benchmarks/quality/` that runs three sources over the M5
  album fixtures and emits a per-field quality report (Markdown file + stdout summary):
  1. **ours** — `parse_album(html)` over the captured fixture HTML.
  2. **ours+LLM** — `ours` plus `enrich_album(album, backend_from_env())`.
  3. **hufman** — the self-hosted hufman/vgmdb service queried over HTTP.
- Define a canonical comparison record (album title/catalog/release_date/publisher/label + per-track
  titles) with per-field normalizers; score each source against the golden as ground truth
  ({match, mismatch, missing, extra}); also emit a raw N-way diff.
- Report ours+LLM as enrichment **coverage** (tracks gaining credits, total credits) — the golden
  has no per-track-credit ground truth.
- hufman is an **optional** column: when the service is unreachable the harness drops it and still
  reports ours vs ours+LLM. hufman runs only as an external Docker service over HTTP
  (`HUFMAN_URL`, default `http://localhost:5000`); no hufman code is vendored or imported.
- Add a smoke test that runs the harness over the fixtures with hufman disabled and no LLM backend
  (no Docker/network in CI).

## Capabilities

### New Capabilities
- `benchmark`: a dev-only parsing-quality harness that compares our parser, our parser + LLM
  enrichment, and a third-party parser against the golden fixtures and reports per-field quality.

### Modified Capabilities
<!-- None: no runtime behavior or existing spec changes. -->

## Impact

- New dev-only code under `benchmarks/quality/` (excluded from the wheel — the build packages only
  `src/vgmdb_client`). No `src/` changes, no M1 schema change.
- No new runtime dependency (httpx, already a runtime dep, covers the hufman HTTP client).
- Reuses `tests.support.fixtures`, `vgmdb_client.parsers.parse_album`, and
  `vgmdb_client.enrich.enrich_album` / `backend_from_env`.
- New smoke + unit tests under `tests/`.
- Operational dependency (dev-time only): a self-hosted hufman/vgmdb Docker service for the hufman
  column; the harness runs without it.
