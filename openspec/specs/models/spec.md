# models Specification

## Purpose
TBD - created by archiving change models-core. Update Purpose after archive.
## Requirements
### Requirement: Multi-language localized text

The models SHALL provide a `LocalizedText` type that wraps a mapping of language label to text
and centralizes language selection. It SHALL expose the full mapping, a preferred-language
lookup, and a default value, and SHALL tolerate an empty mapping.

#### Scenario: Preferred language selected when present

- **WHEN** `prefer("English")` is called on a `LocalizedText` containing an English entry
- **THEN** the English text is returned

#### Scenario: Preferred language falls back when absent

- **WHEN** `prefer("German")` is called and no German entry exists
- **THEN** the default value is returned instead of an error

#### Scenario: Default prefers English then Romaji

- **WHEN** `default` is read on a `LocalizedText` containing Japanese and Romaji but no English
- **THEN** the Romaji text is returned

#### Scenario: Empty text yields no default

- **WHEN** `default` is read on an empty `LocalizedText`
- **THEN** `None` is returned and no error is raised

### Requirement: Partial release dates

The models SHALL provide a `PartialDate` type capturing a required year and optional month and
day, validating ranges and rejecting a day without a month. It SHALL render as `YYYY`,
`YYYY-MM`, or `YYYY-MM-DD` by precision, and SHALL parse those three string shapes.

#### Scenario: Year-only date

- **WHEN** a `PartialDate` is created with only a year
- **THEN** its precision is "year" and it renders as `"YYYY"`

#### Scenario: Day without month rejected

- **WHEN** a `PartialDate` is created with a day but no month
- **THEN** validation fails

#### Scenario: Out-of-range month rejected

- **WHEN** a `PartialDate` is created with month 13
- **THEN** validation fails

#### Scenario: Parsing a partial string

- **WHEN** `PartialDate.parse("2007-08")` is called
- **THEN** a `PartialDate` with year 2007 and month 8 (no day) is returned

#### Scenario: Parsing unparseable input

- **WHEN** `PartialDate.parse` is given a non-date string
- **THEN** `None` is returned

### Requirement: Artist reference

The models SHALL provide an `ArtistRef` lightweight pointer carrying localized names and an
optional id and link, distinct from any full artist entity.

#### Scenario: Reference with id

- **WHEN** an `ArtistRef` is created with names and an id
- **THEN** the names and id are accessible and the link defaults to absent

### Requirement: Album entity

The models SHALL provide an `Album` model covering the core subset of album fields (id, link,
titles, catalog, release date, classification, cover images, discs, credits, notes, and an optional
`release_event`), composed of `Disc`, `Track`, and `Credit` models. Discs SHALL contain tracks. Each
`Credit` SHALL carry a **normalized `role`** (a `Role` value from the controlled vocabulary), a
**verbatim `role_raw`** (the original source label, always present), and a list of artist references.
The optional `release_event` SHALL be an `EventRef` (or `None`) referencing the event the album was
released at.

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
- **THEN** construction succeeds and optional fields default to `None` or empty lists (including
  `release_event` defaulting to `None`)

#### Scenario: Album with a release event

- **WHEN** an `Album` is constructed with a `release_event` `EventRef`
- **THEN** the `release_event` is accessible

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

### Requirement: Album search results

The models SHALL provide `AlbumSearchResult` and a `SearchResults` container carrying the query
and a list of album results.

#### Scenario: Search results carry album entries

- **WHEN** a `SearchResults` is created with a query and album results
- **THEN** the query and the list of `AlbumSearchResult` are accessible

### Requirement: Immutable, unknown-key-rejecting models

All models SHALL be immutable (frozen) and SHALL reject unknown fields at construction.

#### Scenario: Mutation rejected

- **WHEN** code attempts to assign to a field of a constructed model
- **THEN** the assignment raises an error

#### Scenario: Unknown field rejected

- **WHEN** a model is constructed with a field name it does not define
- **THEN** construction raises a validation error

### Requirement: Lightweight entity references

The models SHALL provide lightweight reference types `ProductRef`, `OrgRef`, and `EventRef`, each
wrapping `names` (a `LocalizedText`) with an optional `id` and `link`, mirroring the existing
`ArtistRef`. These point to an entity without embedding its full record.

#### Scenario: A product reference carries name, id, and link

- **WHEN** a `ProductRef` is constructed with names, an id, and a link
- **THEN** all three are accessible and the value is immutable

#### Scenario: A reference may omit id and link

- **WHEN** an `OrgRef` is constructed with only names
- **THEN** `id` and `link` default to `None`

#### Scenario: An event reference mirrors the others

- **WHEN** an `EventRef` is constructed with names and an id
- **THEN** the names and id are accessible and the link defaults to `None`

### Requirement: Artist model

The models SHALL provide an `Artist` model with: `id`, optional `link`, `names` (`LocalizedText`),
`aliases` (list of strings), verbatim `type` (e.g. "Person"/"Unit"), optional `birthdate`
(`PartialDate`), optional `notes`, `members` (list of `ArtistRef`, for a unit), and `units` (list of
`ArtistRef`, groups a person belongs to). It SHALL be immutable and reject unknown fields. List fields
default to empty and optional scalars default to `None`.

#### Scenario: Artist carries identity, metadata, and member refs

- **WHEN** an `Artist` is constructed with names, a verbatim type, a birthdate, and member refs
- **THEN** those values are accessible and `aliases`/`units` default to empty lists

#### Scenario: Artist rejects unknown fields

- **WHEN** an `Artist` is constructed with a field not in its schema
- **THEN** construction fails

### Requirement: Product model

The models SHALL provide a `Product` model with: `id`, optional `link`, `names` (`LocalizedText`),
verbatim `type` (e.g. "Game"/"Franchise"), optional `notes`, `franchises` (list of `ProductRef`), and
`organizations` (list of `OrgRef`). It SHALL be immutable and reject unknown fields; list fields
default to empty and optional scalars default to `None`.

#### Scenario: Product carries metadata and cross-refs

- **WHEN** a `Product` is constructed with names, a type, franchise refs, and organization refs
- **THEN** those values are accessible and absent lists default to empty

### Requirement: Organization model

The models SHALL provide an `Organization` model with: `id`, optional `link`, `names`
(`LocalizedText`), verbatim `type` (e.g. "Company"/"Doujin Circle"/"Label"), and optional `notes`. It
SHALL be immutable and reject unknown fields.

#### Scenario: Organization carries identity and verbatim type

- **WHEN** an `Organization` is constructed with names and a verbatim type
- **THEN** those values are accessible and `notes` defaults to `None`

### Requirement: Event model

The models SHALL provide an `Event` model covering the core subset of event fields: `id`, optional
`link`, localized `names`, optional verbatim `type`, optional `start_date` and `end_date`
(`PartialDate`), and optional `notes`. Released-album and related-entity lists are out of scope.

#### Scenario: Event with dates

- **WHEN** an `Event` is constructed with names, a `start_date`, and an `end_date`
- **THEN** the names and both dates are accessible

#### Scenario: Partial event data is valid

- **WHEN** an `Event` is constructed with only `id` and `names`
- **THEN** construction succeeds and optional fields default to `None`
