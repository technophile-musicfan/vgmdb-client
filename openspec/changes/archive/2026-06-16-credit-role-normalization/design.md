## Context

M1 `Credit` is `{role: str, artists: list[ArtistRef]}` — the role is the verbatim vgmdb label.
Those labels are freeform and unusable for downstream ingestion. This change adds a normalized role
from a controlled vocabulary while preserving the raw label. Source of truth:
`docs/superpowers/vgmdb_client/2026-06-16_credit_role_normalization_design.md`. Models are pure
(no I/O); `pydantic` is already a dependency. The HTML→model parser (M3) will call the helper added
here; this change does not add a parser.

## Goals / Non-Goals

**Goals:**
- A closed `Role` vocabulary (`StrEnum`, ~13 + `OTHER`).
- `normalize_role(raw) -> Role` (conservative, case-insensitive, keyword-based) in the models layer.
- `Credit` carries normalized `role: Role` + verbatim `role_raw: str`.

**Non-Goals:**
- Per-track / freeform-notes credit extraction — B1 (`vgmdb-bzf.1`).
- Organization/Studio as a distinct entity — B3 (studios stay `ArtistRef`).
- The HTML→model parser calling this — M3 (`vgmdb-v9g.6`).
- Confidence scoring — `OTHER` + `role_raw` already encodes uncertainty.

## Decisions

**D1 — Closed `StrEnum` + `OTHER`.** Predictable and queryable; unmapped roles are visible as
`OTHER` with the raw label kept. *Alternatives:* optional enum (None) — rejected, pushes
None-handling to consumers; open canonical slug — rejected, not standardized.

**D2 — Extended vocabulary (~13).** `COMPOSER, ARRANGER, PERFORMER, VOCALIST, LYRICIST, PRODUCER,
ENGINEER, MIXING, MASTERING, DIRECTOR, CONDUCTOR, ARTWORK, OTHER` (values like `"composer"`).
Instruments (Guitar, Violin, …) → `PERFORMER`, specifics preserved in `role_raw`.

**D3 — `Credit` keeps both fields.** `role: Role` (normalized, was `str`), `role_raw: str`
(verbatim, always set), `artists` unchanged. Still `frozen=True, extra="forbid"`. The client's
"verbatim" option is reading `role_raw`.

**D4 — Mapping in the models layer.** New `src/vgmdb_client/models/roles.py` holds `Role` and
`normalize_role` (mirrors `PartialDate.parse` / `LocalizedText.prefer`): shared, unit-testable now,
M3 just calls it. *Alternative:* mapping in the M3 parser only — rejected; untestable/unreusable
until M3, and this change couldn't be verified on its own.

**D5 — Conservative keyword mapping.** Case-insensitive substring/keyword matching; map only on
confident matches, else `OTHER`. Indicative: `compos*`→COMPOSER, `arrang*`→ARRANGER,
`lyric*`/`words`/`written by`→LYRICIST, `vocal*`→VOCALIST, `master*`→MASTERING, `mix*`→MIXING,
`record*`/`engineer`/`pro tools`→ENGINEER, `produc*`→PRODUCER, `conduct*`→CONDUCTOR,
`direct*`→DIRECTOR, `illustrat*`/`art`/`design`/`jacket`→ARTWORK, instruments + `perform*`
→PERFORMER; else `OTHER`. Ordering avoids mis-maps (e.g. check `master`/`mix` before generic
`engineer`). The full table is finalized in implementation against the labels M5 surfaced.

## Risks / Trade-offs

- **Mapping is never perfect** → conservative matching + always-present `role_raw` means a
  miss degrades to `OTHER` + exact raw, not a wrong category. The table is additive (refines
  `OTHER` cases later without breaking frozen models or stored goldens).
- **`Credit` shape change ripples** → consumers must supply `role` + `role_raw`; the ~90 M5 golden
  credit entries are re-authored once this lands (blocked `vgmdb-v9g.5.4`).
- **Vocabulary granularity (~13) may need tuning** → additive; new values/mappings can be added.

## Open Questions

- Exact full mapping table — finalized in implementation against the M5 fixture labels; additive
  afterward.
