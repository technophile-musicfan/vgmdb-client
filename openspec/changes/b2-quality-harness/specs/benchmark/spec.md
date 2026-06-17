## ADDED Requirements

### Requirement: Canonical comparison record

The harness SHALL reduce an album from any source to a canonical record: a flat mapping of field
path to value covering album `title`, `catalog`, `release_date`, and `classification`, plus a
`title` per disc/track addressed as `disc{d}.track{t}.title`. It SHALL provide adapters that build
this record from our parsed `Album`, from the golden `Album`, and from a hufman JSON response. The
hufman adapter SHALL be tolerant: a field absent from the hufman response maps to a missing value
rather than raising.

#### Scenario: Our album reduced to canonical record

- **WHEN** an `Album` is adapted to a canonical record
- **THEN** album-level fields and one entry per track title are present, keyed by their field paths

#### Scenario: Hufman response missing a field

- **WHEN** a hufman JSON response omits a field the record expects
- **THEN** that field path maps to a missing value and no error is raised

### Requirement: Per-field scoring against the golden

The harness SHALL score a source's canonical record against the golden record per field as one of:
`match` (normalized values equal), `mismatch` (both present, normalized values differ), `missing`
(golden has a value, the source does not), or `extra` (the source has a value, the golden does not).
Scoring SHALL apply a per-field normalizer (text strip + casefold, localized text to its default
language, partial date to ISO) so that equivalent values compare equal.

#### Scenario: Matching values score as match

- **WHEN** a source's normalized value for a field equals the golden's
- **THEN** the field scores `match`

#### Scenario: Field absent from source but present in golden

- **WHEN** the golden has a value for a field and the source does not
- **THEN** the field scores `missing`

### Requirement: Enrichment coverage reporting

The harness SHALL report the ours+LLM source as enrichment coverage rather than a golden score,
because the golden carries no per-track-credit ground truth: per album it SHALL report how many
tracks gained credits and the total number of credits extracted. When no LLM backend is configured
the coverage SHALL be reported as not available.

#### Scenario: No backend configured

- **WHEN** the harness runs with no LLM backend configured
- **THEN** the enrichment coverage is reported as not available and the run still completes

#### Scenario: Backend extracts track credits

- **WHEN** a configured backend returns per-track credits for an album
- **THEN** the coverage reports the count of tracks with credits and the total credits

### Requirement: Optional hufman column over HTTP

The harness SHALL obtain hufman results by HTTP GET against a configured base URL (`HUFMAN_URL`,
default `http://localhost:5000`), and SHALL NOT vendor or import any hufman code. When the hufman
service is unreachable, the harness SHALL omit the hufman column and still produce a report for the
remaining sources.

#### Scenario: Hufman service unreachable

- **WHEN** the hufman service cannot be reached
- **THEN** the hufman column is omitted and the report is still produced from the other sources

#### Scenario: Hufman base URL from environment

- **WHEN** `HUFMAN_URL` is set
- **THEN** the harness queries that base URL for album results

### Requirement: Quality report output

The harness SHALL run over the album fixtures and emit a Markdown report containing a scorecard
(per-source field-agreement against the golden), the enrichment-coverage section, and a per-album
field-level N-way diff, and SHALL print a summary (scorecard + coverage) to standard output.

#### Scenario: Report produced over fixtures

- **WHEN** the harness runs over the album fixtures
- **THEN** it writes a Markdown report with a scorecard, coverage, and per-album diff, and prints a
  summary to standard output
