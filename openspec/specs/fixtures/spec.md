# fixtures Specification

## Purpose
A dev-time fixture dataset and loader for vgmdb-client: a dev-only capture script, committed album/search HTML paired with hand-authored golden M1-model JSON, and a test loader plus dataset well-formedness tests. The independent ground truth M3 parsers are built against; no shipped runtime code.

## Requirements
### Requirement: Committed seed fixture dataset

The project SHALL commit a seed dataset of captured vgmdb pages under `tests/fixtures/vgmdb/`,
covering at least 10 album pages and 2 search pages, chosen for structural diversity (e.g.
single-disc, multi-disc, multi-language titles, sparse credits, rich credits, year-only date, full
date, unusual catalog format, freeform-heavy notes; a multi-hit search and a near-empty search).
Album fixtures SHALL live under `albums/` and search fixtures under `search/`.

#### Scenario: Album HTML stored

- **WHEN** the dataset is inspected
- **THEN** at least 10 raw album HTML files exist under `tests/fixtures/vgmdb/albums/`, each
  non-empty

#### Scenario: Search HTML stored

- **WHEN** the dataset is inspected
- **THEN** at least 2 raw search HTML files exist under `tests/fixtures/vgmdb/search/`, each
  non-empty

#### Scenario: Diversity recorded

- **WHEN** the manifest is read
- **THEN** each fixture carries diversity tags describing the structural quirk it covers

### Requirement: Hand-authored golden outputs

Each fixture SHALL have a golden expected output stored alongside its HTML as JSON, authored by
reading the captured HTML directly with no parser involved. Album golden files SHALL be the
`model_dump(mode="json")` form of the expected `Album`; search golden files SHALL be the
corresponding form of the expected `SearchResults`.

#### Scenario: Golden present per fixture

- **WHEN** a captured HTML fixture exists at `<dir>/<name>.html`
- **THEN** a golden JSON file exists at `<dir>/<name>.json`

#### Scenario: Golden validates against its M1 model

- **WHEN** an album golden file is loaded via `Album.model_validate_json` (or a search golden via
  `SearchResults.model_validate_json`)
- **THEN** it parses into a valid M1 model instance with no validation error

### Requirement: Fixture manifest

The dataset SHALL include a `manifest.json` indexing every fixture with its id or slug, kind
(album or search), source URL, captured date, and diversity tags. The manifest SHALL be the single
source of truth for both capture targets and dataset well-formedness checks.

#### Scenario: Manifest matches files on disk

- **WHEN** the manifest entries are compared against the files in `tests/fixtures/vgmdb/`
- **THEN** every manifest entry has corresponding HTML and golden files, and every fixture file on
  disk has a manifest entry (no orphans, no missing)

### Requirement: Dataset documentation

The dataset SHALL include a `README.md` documenting the source (vgmdb.net), the purpose (testing),
the capture date, and a ToS/attribution note.

#### Scenario: README present

- **WHEN** `tests/fixtures/vgmdb/` is inspected
- **THEN** a `README.md` documenting source, purpose, capture date, and attribution is present

### Requirement: Dev-only capture script

The project SHALL provide a dev-only capture script at `scripts/capture_fixtures.py` that fetches
raw vgmdb HTML via the existing `SyncTransport` with the politeness throttle enabled. It SHALL load
credentials from `.env` via `python-dotenv` (`VGMDB_CF_CLEARANCE`, `VGMDB_USER_AGENT`, optional
`VGMDB_BASE_URL`), read its target list from `manifest.json`, and write only raw HTML files. It
SHALL NOT be part of the shipped package and SHALL NOT run in CI. It SHALL be re-runnable, skipping
existing HTML unless an `--overwrite` flag is passed, and SHALL surface transport errors clearly
(e.g. a Cloudflare challenge indicating the token needs refreshing).

#### Scenario: Capture writes raw HTML only

- **WHEN** the capture script runs against a manifest target
- **THEN** it writes the raw HTML to the corresponding `albums/<id>.html` or `search/<slug>.html`
  and writes no golden JSON

#### Scenario: Existing HTML skipped without overwrite

- **WHEN** the capture script runs and a target's HTML already exists and `--overwrite` is not
  passed
- **THEN** that target is skipped and its HTML is left unchanged

#### Scenario: Capture is excluded from the shipped package

- **WHEN** the built/installed package is inspected
- **THEN** `scripts/capture_fixtures.py` is not included as shipped library code

### Requirement: Fixture loader

The project SHALL provide a test/harness loader at `tests/support/fixtures.py` exposing
`iter_album_fixtures()`, `load_album_fixture(id) -> (str, Album)`, and the search equivalents. The
loader SHALL return the raw HTML string paired with the golden parsed into its M1 model instance.

#### Scenario: Load album fixture

- **WHEN** `load_album_fixture(id)` is called for a known album fixture
- **THEN** it returns a tuple of the raw HTML string and a valid `Album` instance parsed from the
  golden JSON

#### Scenario: Iterate fixtures

- **WHEN** `iter_album_fixtures()` is called
- **THEN** it yields every album fixture recorded in the manifest

### Requirement: Dataset well-formedness tests

M5 SHALL include tests asserting the dataset is well-formed: every golden file validates against
its M1 model, the manifest entries match the files present on disk, and each captured HTML file is
present and non-empty. Parser-vs-golden assertions are NOT part of M5 (they arrive with M3).

#### Scenario: Well-formedness suite passes

- **WHEN** the M5 test suite runs
- **THEN** all golden files round-trip through their M1 models, the manifest matches files on disk,
  and every captured HTML file is present and non-empty

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
