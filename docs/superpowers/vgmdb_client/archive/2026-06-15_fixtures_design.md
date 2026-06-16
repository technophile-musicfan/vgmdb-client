# M5 Fixtures — Feature Design

**Date:** 2026-06-15
**Status:** Design (Workflow 2, step 1)
**Epic:** `vgmdb-v9g.5` (M5 Fixtures) — parent `vgmdb-v9g` (MVP)
**Major scope:** `vgmdb_client`
**Vision:** `docs/superpowers/2026-06-14_vgmdb_client.md`
**Depends on:** M1 Models (merged), M2 Transport (merged)

## Purpose

M5 is a **dev-time dataset + loader**: captured vgmdb album/search HTML pages paired with
hand-authored golden expected outputs (typed via M1 models), plus a loader to read them. It is
the ground truth M3 parsers are built against (TDD) and the foundation for the Beta B2 harness.

One sentence: *real vgmdb pages plus the exact models a correct parser must produce from them.*

## Scope

**In scope**
- A dev-only capture script that fetches raw HTML via the transport.
- A committed seed dataset: ~10+ album pages + 2 search pages, chosen for structural diversity.
- Hand-authored golden JSON per fixture (the parser-independent ground truth).
- A test/harness loader and M5's own tests proving the dataset is well-formed.

**Out of scope (tracked elsewhere)**
- The parser and parser-vs-golden assertions → **M3** (`vgmdb-v9g.6`).
- The comparison harness (hufman vs ours vs ours+LLM) → **B2** (`vgmdb-bzf.2`).
- Any runtime/package code — M5 adds no shipped library code.

## Ground-truth workflow (important)

Golden outputs are authored **by reading the captured HTML directly, with no parser involved** —
that is what makes them an independent ground truth rather than a mirror of our parser. The agent
transcribes each page into golden JSON; correctness is then verified by **manual human review**.
Two safety nets:
- **Structural:** every golden file must validate against its M1 model (`model_validate_json`),
  so a shape/type mistake fails loudly.
- **Value:** human review of the golden against the rendered page catches transcription errors
  (e.g. a mistyped track title) that validation cannot.

## Pipeline

```
 capture (dev, one-shot)        committed fixtures              test/harness support
 scripts/capture_fixtures.py    tests/fixtures/vgmdb/...         tests/support/fixtures.py
   reads .env  ───────────────▶   <id>.html  (raw, captured) ◀──  load_album_fixture(id)
   SyncTransport (throttled)      <id>.json  (golden, manual)     → (html, expected Album)
   writes raw HTML only           manifest.json / README.md
```

The capture script only ever writes raw HTML; golden JSON is authored separately by hand.

## Layout

```
tests/fixtures/vgmdb/
  README.md            # source (vgmdb.net), purpose (testing), capture date, ToS/attribution note
  manifest.json        # fixtures index: id/slug, kind, source URL, captured date, diversity tags
  albums/
    <id>.html          # raw captured album page
    <id>.json          # hand-authored golden Album (model_dump JSON)
  search/
    <slug>.html        # raw captured search page
    <slug>.json        # hand-authored golden SearchResults
```

## Golden format

Golden files are the JSON form of the expected model (`model.model_dump(mode="json")`). The loader
reads them via `Album.model_validate_json(text)` / `SearchResults.model_validate_json(text)`,
yielding real M1 model instances. Consequences:
- Golden that does not fit the M1 schema fails loudly at load time.
- Golden stays in lockstep with the models; a model change that breaks a fixture surfaces in tests.

## Capture script

`scripts/capture_fixtures.py` — dev-only, **not** part of the shipped package and **not** run in CI:
- Loads `.env` via **`python-dotenv`** (added as a dev dependency; the runtime library is
  untouched). Reads `VGMDB_CF_CLEARANCE`, `VGMDB_USER_AGENT`, optional `VGMDB_BASE_URL`.
- Reads the target list (album ids + search queries) from `manifest.json`.
- Fetches each via `SyncTransport` with the politeness throttle on; writes `albums/<id>.html` and
  `search/<slug>.html`.
- Re-runnable; existing HTML is skipped unless an `--overwrite` flag is passed.
- Surfaces transport errors clearly (e.g. a `CloudflareChallengeError` means the token needs
  refreshing).

Running it makes real, throttled requests to vgmdb.net using the operator's `.env` token.

## Dataset (~10+ albums + 2 search, broad)

One fixture per structural quirk so M3 gets real edge cases. Target diversity dimensions:
single-disc; multi-disc; English-only titles; multi-language titles (Japanese/Romaji/English);
sparse credits; rich/many-role credits; year-only release date; full release date; unusual catalog
format; freeform-heavy notes. Plus two search pages: a multi-hit query and a near-empty one.

Concrete vgmdb album ids are chosen during implementation and recorded in `manifest.json` with
their diversity tags, source URL, and capture date.

## Test wiring (M5's deliverable)

- `tests/support/fixtures.py`: `iter_album_fixtures()`, `load_album_fixture(id) -> (str, Album)`,
  and the search equivalents.
- Tests:
  - every golden file validates against its M1 model (round-trip),
  - the manifest entries match the files present on disk (no orphans, no missing),
  - each captured HTML file is present and non-empty.
- Parser-vs-golden assertions are **not** part of M5 (they arrive with M3).

## Risks / Trade-offs

- **Hand-authoring effort & transcription error** for 10+ full pages is significant, and M3's
  parser will be built to match golden, so errors propagate. Mitigation: model validation
  (structure) + mandatory human review (values); golden authoring chunked across beads tasks.
- **Committing third-party HTML** grows the repo and stores vgmdb content; kept to a small curated
  set for testing, with a README documenting source/purpose/date.
- **Token-dependent capture** can't run in CI; capture is a manual dev step, but the committed HTML
  makes the *tests* fully reproducible offline.
- **Page structure drift** over time may make a re-capture differ from committed HTML; acceptable —
  fixtures are snapshots, re-captured intentionally.

## Acceptance criteria (from the epic)

- Seed album + search HTML fixtures stored.
- Golden expected model outputs alongside.
- Tests load fixtures (parser assertions deferred to M3; M5 asserts dataset well-formedness).

## Open questions / deferrals

- Exact album ids per diversity dimension — chosen at implementation time, recorded in the manifest.
- Whether the loader later moves out of `tests/` for reuse by the B2 harness — deferred; `tests/`
  is the immediate consumer.
