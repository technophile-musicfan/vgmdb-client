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
titles, catalog, release date, classification, cover images, discs, credits, notes), composed of
`Disc`, `Track`, and `Credit` models. Discs SHALL contain tracks; credits SHALL carry an
open-ended role and a list of artist references.

#### Scenario: Album with tracklist and credits

- **WHEN** an `Album` is constructed with discs (each containing tracks) and credits
- **THEN** the album exposes its discs, their tracks, and its credits

#### Scenario: Credit holds an open-ended role and artists

- **WHEN** a `Credit` is created with role "Arranger" and a list of `ArtistRef`
- **THEN** the role and artists are accessible

#### Scenario: Partial album data is valid

- **WHEN** an `Album` is constructed with only id and titles
- **THEN** construction succeeds and optional fields default to `None` or empty lists

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

