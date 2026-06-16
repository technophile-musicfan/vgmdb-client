# Credit Role Normalization — Feature Design

**Date:** 2026-06-16
**Status:** Design (Workflow 2, step 1)
**Bead:** `vgmdb-v9g.8` (M1.x: Credit role normalization) — parent `vgmdb-v9g` (MVP)
**Major scope:** `vgmdb_client`
**Vision:** `docs/superpowers/2026-06-14_vgmdb_client.md`
**Depends on:** M1 Models (merged)
**Blocks:** M5 Fixtures golden-credit finalization (`vgmdb-v9g.5.4`)

## Purpose

Extend the M1 `Credit` model so consumers get a **normalized role** from a controlled vocabulary
**and** the **verbatim source label**. vgmdb credit labels are freeform ("Original Music Composed
by", "Words", "Music", "Recording Studio", "Performed by"); a client trying to fill a "composer"
field cannot ingest those, but a wrong normalization could surprise users — so we keep both.

Discovered during M5 golden authoring, where verbatim role labels (271, 45000, …) were recorded
as-is and found unusable for downstream ingestion.

## Scope

**In scope**
- A `Role` enum (controlled vocabulary, closed set + `OTHER`).
- `Credit` gains `role: Role` (normalized) + `role_raw: str` (verbatim); `artists` unchanged.
- A `normalize_role(raw) -> Role` helper + mapping table in the models layer.
- Unit tests for the mapping and the model change.

**Out of scope (tracked elsewhere)**
- Per-track / freeform-notes credit extraction → **B1** (`vgmdb-bzf.1`), incl. the per-track
  credits embedded in notes (e.g. album 271 tracks 10/11/27, album 33000).
- A distinct Organization/Studio entity (studios/venues remain `ArtistRef`) → **B3**.
- Confidence scoring — `OTHER` + `role_raw` already represents "uncertain".
- The HTML→model parser that *calls* `normalize_role` → **M3** (`vgmdb-v9g.6`).

## Decisions

**D1 — Normalized role is a closed `StrEnum` + `OTHER`.**
Predictable and queryable; anything unmapped is visible as `OTHER` with the raw label preserved.
*Alternatives:* optional enum (None when unsure) — rejected, pushes None-handling onto every
consumer; open canonical slug — rejected, not standardized/queryable.

**D2 — Extended vocabulary (~13 values).**
`COMPOSER, ARRANGER, PERFORMER, VOCALIST, LYRICIST, PRODUCER, ENGINEER, MIXING, MASTERING,
DIRECTOR, CONDUCTOR, ARTWORK, OTHER` (string values like `"composer"`). Instruments (Guitar,
Violin, Cello, …) map to `PERFORMER` with specifics kept in `role_raw`.

**D3 — `Credit` keeps both fields.**
```
role: Role                  # normalized (was: role: str)
role_raw: str               # verbatim source label, always set
artists: list[ArtistRef]    # unchanged
```
Still `frozen=True, extra="forbid"`. The client's "verbatim" option is simply reading `role_raw`.

**D4 — Mapping logic lives in the models layer.**
A new module `src/vgmdb_client/models/roles.py` holds the `Role` enum and
`normalize_role(raw: str) -> Role` (mirrors `PartialDate.parse` / `LocalizedText.prefer`):
shared, unit-testable now (before M3 exists), and M3's parser just calls it. One source of truth.
*Alternative:* mapping in the M3 parser only — rejected; untestable/unreusable until M3, and this
change couldn't be verified end-to-end on its own.

**D5 — Conservative, keyword-based, case-insensitive mapping.**
Map only on confident keyword matches; otherwise `OTHER`. Indicative table (full table is an
implementation detail): `compos*`→COMPOSER, `arrang*`→ARRANGER, `lyric*`/`words`/`written by`
→LYRICIST, `vocal*`→VOCALIST, `master*`→MASTERING, `mix*`→MIXING,
`record*`/`engineer`/`pro tools`→ENGINEER, `produc*`→PRODUCER, `conduct*`→CONDUCTOR,
`direct*`→DIRECTOR, `illustrat*`/`art`/`design`/`jacket`→ARTWORK, instruments + `perform*`
→PERFORMER; else `OTHER`. Conservative matching means a wrong/ambiguous label degrades to
`OTHER` + exact raw rather than a misleading category.

## Data flow

```
HTML credit label ──(M3 parser, later)──▶ role_raw (verbatim, str)
                                              │
                                   normalize_role(role_raw)
                                              ▼
                                         role (Role enum)
```
In M5 goldens, `role_raw` is hand-transcribed ground truth and `role` is its normalized value
(human-reviewed). `normalize_role` is shared by goldens and the future M3 parser, so the
meaningful checks are (a) `role_raw` extraction from HTML and (b) the `normalize_role` unit tests.

## Testing

- `normalize_role` unit tests over the real labels M5 surfaced: Composer / Arranger / "Performed
  by" / Vocals / Words / "Mastering Studio" / "Recording Studio" / instrument names /
  "Special Thanks"→OTHER, plus case-insensitivity and unknown→OTHER.
- Model tests: `Credit` requires `role_raw`, accepts a valid `Role`, rejects an invalid enum and
  unknown keys; immutability preserved.
- `ruff`, `mypy`, full suite green.

## Risks / Trade-offs

- **Mapping is never perfect** → conservative matching + `role_raw` always present means misses
  degrade to `OTHER` + raw, not a wrong category. The table is additive — new mappings don't break
  frozen models or stored goldens (only refine `OTHER` cases).
- **`Credit` shape change ripples to M5 goldens** → the ~90 golden credit entries are re-authored
  to `{role, role_raw, artists}` once this lands; this is the blocked `vgmdb-v9g.5.4`.
- **Vocabulary granularity** (~13) may need tuning as more pages are seen → additive; new enum
  values or mappings can be added later.

## Acceptance criteria

- `Role` enum (~13 + OTHER) and `normalize_role` implemented in `models/roles.py`.
- `Credit` exposes normalized `role` + verbatim `role_raw`; vocabulary + mapping defined and tested.
- `ruff` + `mypy` + full test suite green.
- (Follow-on, separate) M5 goldens re-authored against the new shape.

## Open questions / deferrals

- Exact full mapping table contents — finalized in implementation against the labels in the M5
  fixtures; additive afterward.
