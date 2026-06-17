# benchmark Specification

## Purpose
A dev-only parsing-quality harness (under `benchmarks/`, never shipped) that compares our parser, our parser + LLM enrichment, and a third-party parser (self-hosted hufman/vgmdb over HTTP) against the golden fixtures, and emits a per-field quality report (Markdown + stdout summary). hufman is an optional column queried over HTTP and is never vendored or imported into the runtime.

## Requirements

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

### Requirement: Enrichment credit-matching scorer

The harness SHALL score an `AlbumEnrichment` against an enrichment golden, producing precision,
recall, and F1 over per-track credits. Two credits match when they share the same track number and
the same normalized `Role` and their artist-name sets overlap (compared casefolded). Precision is
matched / produced and recall is matched / golden; when a denominator is zero the corresponding
metric is defined as 1.0, so an empty golden scored against empty output is perfect and an empty
golden scored against produced credits yields precision below 1 (a hallucination penalty).

#### Scenario: Exact match scores perfectly

- **WHEN** a backend's enrichment equals the golden
- **THEN** precision, recall, and F1 are all 1.0

#### Scenario: Hallucination against an empty golden

- **WHEN** the golden is empty but the backend produces a credit
- **THEN** precision is below 1.0 (recall remains defined)

#### Scenario: Partial recall

- **WHEN** a backend produces a subset of the golden's credits
- **THEN** recall is below 1.0 and precision is 1.0

### Requirement: Multi-backend enrichment reporting

The harness SHALL accept a mapping of named enrichment backends and SHALL report an "Enrichment
quality" section ranking each backend by precision / recall / F1 against the enrichment goldens, per
album and in aggregate. The existing coverage reporting SHALL remain.

#### Scenario: Ranking multiple named backends

- **WHEN** the harness runs with more than one named backend
- **THEN** the report lists each backend's enrichment precision / recall / F1

#### Scenario: No backends configured

- **WHEN** the harness runs with no enrichment backends
- **THEN** the enrichment-quality section reports that no backends were configured and the run still
  completes
