## Context

M5 is a **dev-time dataset + loader**: captured vgmdb album/search HTML paired with hand-authored
golden expected outputs (typed via M1 models), plus a loader to read them. It is the ground truth
M3 parsers are built against (TDD) and the foundation for the B2 parsing-quality harness. It adds
**no shipped runtime/library code**. Source of truth:
`docs/superpowers/vgmdb_client/2026-06-15_fixtures_design.md`.

Dependencies are already merged: M1 models (`Album`, `SearchResults`, …) and M2 transport
(`SyncTransport`, throttled, Cloudflare-token aware). `pydantic` is already a runtime dependency.

The defining constraint: golden outputs must be an **independent** ground truth, authored by
reading the captured HTML directly with **no parser involved** — otherwise they would merely mirror
the parser they are meant to validate.

## Goals / Non-Goals

**Goals:**
- A dev-only capture script that fetches raw HTML via the transport and writes only raw HTML.
- A committed seed dataset: ~10+ album pages + 2 search pages, chosen for structural diversity.
- Hand-authored golden JSON per fixture, validated against its M1 model.
- A test/harness loader and M5's own tests proving the dataset is well-formed.

**Non-Goals:**
- The HTML→model parser and parser-vs-golden assertions — M3 (`vgmdb-v9g.6`).
- The comparison harness (hufman vs ours vs ours+LLM) — B2 (`vgmdb-bzf.2`).
- Any shipped runtime/package code — M5 adds none.

## Decisions

**D1 — Golden authored from HTML by hand, verified by human review.**
The agent transcribes each captured page into golden JSON with no parser involved; correctness is
confirmed by **manual human review** of the golden against the rendered page. Two safety nets:
structural (`model_validate_json` rejects shape/type mistakes loudly) and value (human review
catches transcription errors validation cannot, e.g. a mistyped track title). *Alternative:*
generate golden from a draft parser — rejected; it makes golden a mirror of the parser, destroying
its value as independent ground truth.

**D2 — Golden stored as `model.model_dump(mode="json")`; loaded via `model_validate_json`.**
The loader returns real M1 model instances, so golden that does not fit the M1 schema fails loudly
at load time and golden stays in lockstep with the models — a model change that breaks a fixture
surfaces in tests. *Alternative:* a bespoke golden schema — rejected; it would drift from the
models and need its own validation.

**D3 — Capture script is dev-only, writes raw HTML only.**
`scripts/capture_fixtures.py` lives outside the shipped package and is never run in CI. It reads
`.env` via `python-dotenv` (`VGMDB_CF_CLEARANCE`, `VGMDB_USER_AGENT`, optional `VGMDB_BASE_URL`),
reads the target list from `manifest.json`, fetches each via `SyncTransport` with the politeness
throttle on, and writes only `albums/<id>.html` / `search/<slug>.html`. Re-runnable; existing HTML
is skipped unless `--overwrite` is passed. Transport errors surface clearly (a
`CloudflareChallengeError` means the token needs refreshing). *Alternative:* committing a token or
running capture in CI — rejected; tokens are operator secrets and expire, and committed HTML makes
the *tests* fully reproducible offline without capture.

**D4 — `manifest.json` is the single source of truth for the dataset.**
It indexes every fixture (id/slug, kind, source URL, captured date, diversity tags) and drives both
the capture target list and the well-formedness tests (manifest entries must match files on disk —
no orphans, no missing). *Alternative:* infer the dataset from directory listing — rejected; loses
provenance (source URL, capture date) and diversity intent.

**D5 — Loader and tests live under `tests/`.**
`tests/support/fixtures.py` exposes `iter_album_fixtures()`, `load_album_fixture(id) -> (str,
Album)`, and the search equivalents. The immediate consumer is the test suite; whether the loader
later moves out of `tests/` for the B2 harness is deferred and additive. *Alternative:* ship the
loader in the library now — rejected; premature, and M5 is explicitly no-shipped-code.

**D6 — `python-dotenv` added as a dev dependency only.**
Capture needs `.env` loading; the runtime library must stay untouched. *Alternative:* hand-roll
`.env` parsing — rejected; `python-dotenv` is standard and dev-only.

## Risks / Trade-offs

- **Hand-authoring effort & transcription error** for 10+ full pages is significant, and M3's
  parser will be built to match golden, so errors propagate → mitigated by model validation
  (structure) + mandatory human review (values); golden authoring chunked across beads tasks.
- **Committing third-party HTML** grows the repo and stores vgmdb content → kept to a small curated
  set for testing, with a `README.md` documenting source/purpose/capture-date/ToS-attribution.
- **Token-dependent capture can't run in CI** → capture is a manual dev step; the committed HTML
  makes the tests fully reproducible offline.
- **Page-structure drift** over time may make a re-capture differ from committed HTML → acceptable;
  fixtures are intentional snapshots, re-captured deliberately.

## Open Questions

- Exact album ids per diversity dimension — chosen at implementation time, recorded in the manifest.
- Whether the loader later moves out of `tests/` for reuse by the B2 harness — deferred; `tests/`
  is the immediate consumer.
