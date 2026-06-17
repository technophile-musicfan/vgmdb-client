# B2 Parsing-Quality Harness — Design

**Bead:** vgmdb-bzf.2 · **Date:** 2026-06-17 · **Workflow:** 2 (light path — no schema change, single subsystem)

## Purpose

Measure how well our parser extracts vgmdb album data, by comparing three sources over the committed
fixture dataset and emitting a per-field quality report:

1. **ours** — `parse_album(html)` over the captured fixture HTML.
2. **ours+LLM** — `ours` plus `enrich_album(album, backend_from_env())` (B1 deep-parse overlay).
3. **hufman** — the self-hosted [hufman/vgmdb](https://github.com/hufman/vgmdb) (vgmdb.info) service,
   queried over HTTP, as an independent third-party benchmark.

The golden JSON authored in M5 is the ground truth for **structural** fields. The report ranks
parser quality against that ground truth and surfaces where the three disagree.

## Constraints & non-goals

- **hufman never enters the runtime library.** It runs as an external Docker service; we only make
  HTTP requests to it. No hufman Python code is vendored or imported.
- **Dev-only.** The harness lives under `benchmarks/`, which is excluded from the wheel (the build
  packages only `src/vgmdb_client`). No new runtime dependency; httpx (already a runtime dep) covers
  the hufman HTTP client.
- **No schema change.** Reuses M1 models, the M3 parsers, the B1 enrichment, and the M5 fixtures.
- Not a pass/fail gate on parser quality — it is a measurement/reporting tool run on demand.

## Known limitations (documented, accepted for this iteration)

- **hufman parses live vgmdb; our fixtures are a snapshot.** hufman has no "parse this HTML"
  endpoint — it scrapes vgmdb.net itself. So hufman reflects the *current* live page while we parse
  the captured bytes. For stable albums this is fine; it is not byte-identical. The hufman column is
  therefore **optional**: if the service is unreachable (down or Cloudflare-blocked), the harness
  drops the hufman column and still reports ours vs ours+LLM. Priming hufman's cache with the
  fixture HTML for byte-identical comparison is a deferred future enhancement.
- **ours+LLM has no golden ground truth.** The goldens are the M3 structural parse; per-track
  credits (what B1 enrichment extracts from freeform notes) are deliberately not in the golden. So
  ours+LLM is identical to ours on every scored field. Its value is reported as **coverage**
  (tracks that gained credits, total credits extracted), not as a vs-golden score.

## Architecture

A standalone harness under `benchmarks/quality/`, composed of focused single-purpose modules:

| Module | Responsibility |
|---|---|
| `fields.py` | The canonical comparison record: the flat set of compared fields + a per-field normalizer. |
| `adapters.py` | Map each source to a canonical record: `from_album(Album)` (ours), `from_golden(Album)`, `from_hufman(dict)` (tolerant, best-effort). |
| `hufman_client.py` | httpx GET to `HUFMAN_URL`; returns the album JSON dict or `None` if unreachable. |
| `compare.py` | Per-field scoring vs golden ({match, mismatch, missing, extra}) + build the raw N-way diff rows + enrichment coverage. |
| `report.py` | Render the Markdown report and the stdout summary. |
| `run.py` | Entry point: iterate fixtures → parse ours → enrich (optional) → fetch hufman (optional) → compare → write report. |

Dependencies it reuses: `tests.support.fixtures` (fixture loader), `vgmdb_client.parsers.parse_album`,
`vgmdb_client.enrich.enrich_album` / `backend_from_env`.

## Comparison model

A **canonical record** is a flat mapping `field_path -> value`:

- Album level: `title`, `catalog`, `release_date`, `publisher`, `label`.
- Per track: `disc{d}.track{t}.title`.

Each field has a **normalizer** used only for *scoring* (fair comparison), e.g. strip + casefold for
text, `LocalizedText -> default-language string`, `PartialDate -> ISO string`. The raw N-way diff
keeps the **un-normalized** values so real divergences stay visible.

Per-field score vs golden:

- **match** — normalized value equals golden's.
- **mismatch** — both present, normalized values differ.
- **missing** — golden has a value, this source does not.
- **extra** — this source has a value, golden does not. (Reported, not penalized.)

## Configuration

- `HUFMAN_URL` (env) — base URL of the self-hosted hufman service; default `http://localhost:5000`.
  Unset/unreachable → hufman column skipped.
- `LLM_URL` / `LLM_MODEL` / `LLM_API_KEY` (env, via existing `backend_from_env`) — drives the
  ours+LLM column. No `LLM_URL` → coverage column reads "n/a (no backend)".

## Report

Markdown file at `benchmarks/quality/report.md` (gitignored), three sections:

1. **Scorecard** — parser × field-agreement % vs golden (ours, hufman). Ranks structural quality.
2. **Enrichment coverage** — ours+LLM: per album, tracks-with-credits / total tracks, total credits.
   Flagged "no golden ground truth."
3. **Per-album field detail** — an N-way table per album (golden | ours | hufman | ours+LLM
   where applicable), showing each field's value and its score, so divergences are inspectable.

Stdout prints the scorecard + coverage summary only.

## Testing

A smoke test under `tests/` runs the harness over the fixtures with **hufman disabled** and **no LLM
backend** (no Docker, no network in CI), asserting it builds a report containing the expected
ours-vs-golden scorecard rows and completes cleanly. The hufman client and LLM backend are exercised
through their optional/absent paths (returning `None`), so CI never touches the network. Adapter and
comparator units get focused tests (e.g. `from_hufman` tolerant mapping, normalizer behavior,
match/mismatch/missing scoring).

## Out of scope (future)

- Search-result comparison (this iteration is album-only; the structure generalizes later).
- Cache-priming hufman with fixture HTML for byte-identical comparison.
- Aggregate cross-album trend tracking / historical reports.
