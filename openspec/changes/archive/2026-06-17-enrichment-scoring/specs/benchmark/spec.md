## ADDED Requirements

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
