# vgmdb test fixtures

Captured vgmdb.net pages paired with hand-authored golden expected outputs, used as the
ground-truth dataset for the parser (M3) and the parsing-quality harness (B2).

## What's here

```
manifest.json     # index of every fixture: id/slug, kind, source URL, captured date, diversity tags
albums/<id>.html  # raw captured album page
albums/<id>.json  # hand-authored golden Album  (model_dump(mode="json"))
search/<slug>.html# raw captured search page
search/<slug>.json# hand-authored golden SearchResults
```

`manifest.json` is the single source of truth: the capture script reads its target list from it,
and the well-formedness tests check it against the files on disk.

## Source, purpose & attribution

- **Source:** https://vgmdb.net — a community database of video-game and anime music.
- **Purpose:** development/testing only. These pages are committed so the test suite is fully
  reproducible offline (capture needs a live Cloudflare token and cannot run in CI).
- **Attribution / ToS:** content is © vgmdb.net and its contributors. Only a small curated set is
  stored, solely to test this client's parsing. Do not redistribute beyond this purpose. Capture is
  throttled to be polite. If asked by vgmdb.net to remove this content, do so.
- **Capture date:** recorded per-fixture in `manifest.json` (`captured_date`). Fixtures are
  intentional snapshots; page structure may drift over time and is re-captured deliberately.

## Capturing / refreshing

Capture is a manual dev step (not run in CI):

1. `cp example.env .env` and fill in `VGMDB_CF_CLEARANCE` + `VGMDB_USER_AGENT` (see `example.env`).
2. `uv run python scripts/capture_fixtures.py` — fetches every manifest target via the throttled
   `SyncTransport` and writes raw HTML only. Existing HTML is skipped unless `--overwrite` is passed.

> **Candidate ids:** album ids in `manifest.json` start as `status: "candidate"` with an *intended*
> diversity dimension. Confirm each live page actually exhibits its tagged quirk; swap the id if it
> doesn't, then set `status: "captured"` and fill `captured_date`.

## Golden outputs

> **Search `multi-hit` is a first-N sample.** Its page lists 1106 album results; the golden
> transcribes only the **first 10 rows** (in page order). The manifest entry records this via
> `golden_scope: "first-10"`, so any parser-vs-golden comparison (M3/B2) must compare against the
> first 10 results only. `near-empty` is the 0-results case (`albums: []`).

Golden JSON is authored **by hand, by reading the captured HTML directly — no parser involved** —
so it is an independent ground truth rather than a mirror of our parser. Each golden is the
`model_dump(mode="json")` form of the expected M1 model and is loaded via `model_validate_json`, so
a shape/type mistake fails loudly. A human review pass against the rendered page catches
transcription errors (e.g. a mistyped track title) that validation cannot.
