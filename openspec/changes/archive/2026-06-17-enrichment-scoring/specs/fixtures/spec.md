## ADDED Requirements

### Requirement: Per-album enrichment goldens

The project SHALL commit a hand-authored enrichment golden for every album fixture under
`tests/fixtures/vgmdb/enrichment/<album_id>.json`, each a serialized `AlbumEnrichment` (album id and
per-track credits keyed by track number) derived from the album's freeform notes. Albums whose notes
attribute credits to specific tracks SHALL have those credits transcribed; albums without
track-attributed credits SHALL have an empty enrichment (negative ground truth). The loader SHALL
validate each golden against the `AlbumEnrichment` model on load.

#### Scenario: Enrichment golden loads and validates

- **WHEN** an album fixture's enrichment golden is loaded
- **THEN** it is returned as a validated `AlbumEnrichment` for that album id

#### Scenario: Every album fixture has an enrichment golden

- **WHEN** the album fixtures are enumerated
- **THEN** each has a corresponding enrichment golden (empty when no track-attributed credits exist)

### Requirement: Enrichment golden loaders

The fixture loader SHALL expose `load_enrichment_golden(album_id) -> AlbumEnrichment` and
`iter_enrichment_goldens()` yielding the album ids that have an enrichment golden.

#### Scenario: Iterate enrichment goldens

- **WHEN** `iter_enrichment_goldens()` is called
- **THEN** it yields the album ids for which an enrichment golden is committed
