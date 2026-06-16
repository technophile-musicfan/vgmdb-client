## MODIFIED Requirements

### Requirement: Album entity

The models SHALL provide an `Album` model covering the core subset of album fields (id, link,
titles, catalog, release date, classification, cover images, discs, credits, notes), composed of
`Disc`, `Track`, and `Credit` models. Discs SHALL contain tracks. Each `Credit` SHALL carry a
**normalized `role`** (a `Role` value from the controlled vocabulary), a **verbatim `role_raw`**
(the original source label, always present), and a list of artist references.

#### Scenario: Album with tracklist and credits

- **WHEN** an `Album` is constructed with discs (each containing tracks) and credits
- **THEN** the album exposes its discs, their tracks, and its credits

#### Scenario: Credit carries a normalized role and the verbatim label

- **WHEN** a `Credit` is created with `role` `Role.ARRANGER`, `role_raw` "Arrangement", and a list
  of `ArtistRef`
- **THEN** the normalized role, the verbatim `role_raw`, and the artists are all accessible

#### Scenario: Credit requires the verbatim label

- **WHEN** a `Credit` is constructed without `role_raw`
- **THEN** construction fails (the verbatim label is required)

#### Scenario: Partial album data is valid

- **WHEN** an `Album` is constructed with only id and titles
- **THEN** construction succeeds and optional fields default to `None` or empty lists

## ADDED Requirements

### Requirement: Normalized credit roles

The models SHALL provide a closed `Role` vocabulary (a `StrEnum` of `COMPOSER, ARRANGER, PERFORMER,
VOCALIST, LYRICIST, PRODUCER, ENGINEER, MIXING, MASTERING, DIRECTOR, CONDUCTOR, ARTWORK, OTHER`) and
a `normalize_role(raw)` function that maps a freeform vgmdb role label to a `Role`. Mapping SHALL be
case-insensitive and conservative: a label that does not confidently match a known role SHALL map
to `OTHER`. The verbatim label is never discarded — it is preserved on `Credit.role_raw`.

#### Scenario: Known label maps to its normalized role

- **WHEN** `normalize_role` is called with "Original Music Composed by"
- **THEN** it returns `Role.COMPOSER`

#### Scenario: Instrument performer maps to PERFORMER

- **WHEN** `normalize_role` is called with an instrument credit such as "Acoustic Guitar"
- **THEN** it returns `Role.PERFORMER` (the specific instrument remains in `role_raw`)

#### Scenario: Matching is case-insensitive

- **WHEN** `normalize_role` is called with "ARRANGEMENT" and with "arrangement"
- **THEN** both return `Role.ARRANGER`

#### Scenario: Unrecognized label maps to OTHER

- **WHEN** `normalize_role` is called with a label that matches no known role, such as
  "Special Thanks"
- **THEN** it returns `Role.OTHER`
