## ADDED Requirements

### Requirement: Rule-based enrichment backend

The package SHALL provide a deterministic `RuleBasedBackend` implementing the `EnrichmentBackend`
protocol (`enrich(album, raw_text) -> AlbumEnrichment`) with no additional dependency. It SHALL
extract per-track credits from the album's freeform notes by parsing track-range notations
(comma lists, `~` ranges, `M`/`M-`/leading-zero prefixes), an inline-parenthetical pattern
(`<Name> (<ranges>)` under a role context), and a block pattern (a track-range/number header line
sets the current track set and subsequent role lines attribute to it). Extracted role labels SHALL be
normalized via `normalize_role`.

A role line SHALL emit credits only when it has a track context (a preceding range/number header) or
an inline range; credits with no track reference (album-level) SHALL be dropped. The backend SHALL be
deterministic and SHALL NOT perform any network access.

#### Scenario: Block pattern attributes a role line to a preceding range header

- **WHEN** notes contain a track-range header followed by a `<Role> by <Names>` line
- **THEN** the named artists are credited (with the normalized role) to every track in that range

#### Scenario: Inline parenthetical attributes names to their ranges

- **WHEN** notes contain `<Role>: <Name> (<ranges>)` groups
- **THEN** each name is credited to the tracks in its parenthetical range

#### Scenario: Album-level credit without a track reference is dropped

- **WHEN** notes contain a role/credit line with no track range or number context
- **THEN** no credit is emitted for it (the enrichment stays empty for that content)

#### Scenario: Track-range notations are parsed

- **WHEN** a range is written as a comma list, a `~` range, or with `M`/`M-`/leading-zero prefixes
- **THEN** it resolves to the corresponding set of track numbers
