## Why

M3 parsers must be built and verified against real vgmdb pages plus the exact models a correct
parser should produce from them. Without a committed, validated ground-truth dataset there is
nothing to drive M3's TDD or to anchor the later B2 parsing-quality harness. This change captures
that dataset: real captured HTML paired with hand-authored golden outputs typed via M1 models.

## What Changes

- Add a **dev-only capture script** (`scripts/capture_fixtures.py`) that fetches raw vgmdb HTML via
  the existing `SyncTransport` (throttled), reading credentials from `.env`. Not shipped in the
  package, not run in CI.
- Commit a **seed fixture dataset** under `tests/fixtures/vgmdb/`: ~10+ album pages + 2 search
  pages, chosen for structural diversity (single/multi-disc, multi-language titles, sparse/rich
  credits, partial/full dates, unusual catalog formats, freeform notes; multi-hit + near-empty
  search).
- Author **hand-transcribed golden JSON** per fixture — the parser-independent ground truth — as
  `model.model_dump(mode="json")` form of the expected M1 model.
- Add a **test/harness loader** (`tests/support/fixtures.py`) and M5's own tests proving the
  dataset is well-formed (golden round-trips through M1 models, manifest matches files on disk,
  every captured HTML present and non-empty).
- Add **`python-dotenv` as a dev dependency** (the runtime library is untouched).

Out of scope (tracked separately): the HTML→model parser and parser-vs-golden assertions → M3
(`vgmdb-v9g.6`); the comparison harness (hufman vs ours vs ours+LLM) → B2 (`vgmdb-bzf.2`); any
shipped runtime/library code — M5 adds none.

## Capabilities

### New Capabilities
- `fixtures`: A dev-time fixture dataset and loader for vgmdb-client — a capture script that fetches
  raw vgmdb HTML via the transport, a committed seed dataset of album/search HTML paired with
  hand-authored golden M1-model JSON, and a test loader plus dataset well-formedness tests. The
  ground truth M3 parsers are built against; no shipped runtime code.

### Modified Capabilities
<!-- None — `models` and `transport` are consumed unchanged. -->

## Impact

- **New dev tooling:** `scripts/capture_fixtures.py` (dev-only, excluded from the shipped package
  and from CI).
- **New test assets:** `tests/fixtures/vgmdb/` (captured HTML + golden JSON + `manifest.json` +
  `README.md`) and `tests/support/fixtures.py` (loader) with accompanying well-formedness tests.
- **Dependencies:** adds `python-dotenv` as a **dev** dependency only; no new runtime dependency.
  Consumes existing `SyncTransport` (M2) and M1 models unchanged.
- **Downstream:** unblocks M3 Parsers (`vgmdb-v9g.6`) and the B2 parsing-quality harness
  (`vgmdb-bzf.2`).
