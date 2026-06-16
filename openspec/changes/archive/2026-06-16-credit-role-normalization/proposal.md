## Why

vgmdb credit role labels are freeform ("Original Music Composed by", "Words", "Music", "Recording
Studio", "Performed by"). A client trying to fill a structured field like "composer" cannot ingest
those raw strings, but a wrong normalization could mislead users. The `Credit` model therefore
needs a **normalized role** from a controlled vocabulary **and** the preserved **verbatim label**.
Surfaced during M5 golden authoring, where verbatim roles proved unusable downstream.

## What Changes

- Add a **`Role` enum** (closed `StrEnum`, ~13 values + `OTHER`): `COMPOSER, ARRANGER, PERFORMER,
  VOCALIST, LYRICIST, PRODUCER, ENGINEER, MIXING, MASTERING, DIRECTOR, CONDUCTOR, ARTWORK, OTHER`.
- Add a **`normalize_role(raw: str) -> Role`** helper + mapping table in a new
  `src/vgmdb_client/models/roles.py` (mirrors `PartialDate.parse`). Conservative, case-insensitive,
  keyword-based; anything not confidently matched → `OTHER`.
- **BREAKING (internal): change `Credit`** from `role: str` to `role: Role` (normalized) and add
  `role_raw: str` (verbatim source label, always set); `artists` unchanged. Still `frozen` /
  `extra="forbid"`.
- Export the new public surface (`Role`, `normalize_role`) from `models/__init__.py`.

Out of scope (tracked separately): per-track / freeform-notes credit extraction → B1
(`vgmdb-bzf.1`); a distinct Organization/Studio entity → B3 (`vgmdb-bzf.3`); the HTML→model parser
that will call `normalize_role` → M3 (`vgmdb-v9g.6`). No confidence scoring — `OTHER` + `role_raw`
represents uncertainty.

## Capabilities

### New Capabilities
<!-- None — this extends the existing `models` capability. -->

### Modified Capabilities
- `models`: The `Credit` model gains a normalized `role` (controlled `Role` vocabulary) plus a
  verbatim `role_raw`, and the layer gains a `Role` enum and a `normalize_role` mapping helper.

## Impact

- **Code:** new `src/vgmdb_client/models/roles.py` (`Role` + `normalize_role`); `Credit` in
  `album.py` changes shape; `models/__init__.py` re-exports.
- **Dependencies:** none new.
- **Downstream:** M3 parser will call `normalize_role`; **M5 fixtures** golden credit entries
  (~90) are re-authored to `{role, role_raw, artists}` once this lands (blocks `vgmdb-v9g.5.4`).
- **Consumers:** any code constructing `Credit` must now supply `role` (a `Role`) + `role_raw`.
