## ADDED Requirements

### Requirement: Lightweight entity references

The models SHALL provide lightweight reference types `ProductRef` and `OrgRef`, each wrapping
`names` (a `LocalizedText`) with an optional `id` and `link`, mirroring the existing `ArtistRef`.
These point to an entity without embedding its full record.

#### Scenario: A product reference carries name, id, and link

- **WHEN** a `ProductRef` is constructed with names, an id, and a link
- **THEN** all three are accessible and the value is immutable

#### Scenario: A reference may omit id and link

- **WHEN** an `OrgRef` is constructed with only names
- **THEN** `id` and `link` default to `None`

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
