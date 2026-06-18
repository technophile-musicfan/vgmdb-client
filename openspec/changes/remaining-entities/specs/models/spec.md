## ADDED Requirements

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

## MODIFIED Requirements

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
