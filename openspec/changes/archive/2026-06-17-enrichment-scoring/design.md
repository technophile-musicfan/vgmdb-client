## Context

B2's harness can only report enrichment coverage (no ground truth), so backends cannot be scored or
compared. Full design:
`docs/superpowers/vgmdb_client/2026-06-17_enrichment_scoring_design.md`. This is Cycle 1 of the
Enrichment v2 epic (vgmdb-zsy); Cycles 2 (LLM backend v2) and 3 (lightweight + optional ML backends)
follow and consume this cycle's scorer.

## Goals / Non-Goals

**Goals:**
- Per-album enrichment goldens (populated + empty/negative), validated against `AlbumEnrichment`.
- A precision/recall/F1 credit-matching scorer.
- A harness that runs multiple **named** backends and reports enrichment quality side by side.

**Non-Goals:**
- New backends (Cycles 2–3); Cycle 1 uses stub backends, no network in CI.
- Changing `AlbumEnrichment` or the `EnrichmentBackend` protocol.

## Decisions

- **Golden storage.** `tests/fixtures/vgmdb/enrichment/<album_id>.json` = a serialized
  `AlbumEnrichment` (`album_id` + `track_credits` keyed by track number), hand-authored from the
  album's `notes`. Every album fixture gets one; most are empty, a few populated. Validated against
  the model on load (fails loudly on drift). Loaders `load_enrichment_golden` / `iter_enrichment_goldens`.
- **Credit identity for matching:** `(track_number, normalized Role, frozenset of casefolded artist
  names)`. Two credits match when track number and `Role` are equal and their artist-name sets
  overlap (casefolded). Role wording is already collapsed by `normalize_role`; name overlap (not
  equality) softens phrasing differences.
- **Metrics:** per album and aggregate `precision = matched/produced`, `recall = matched/golden`,
  `F1`. Empty golden + empty output = perfect (precision and recall defined as 1.0 when the relevant
  denominator is 0); empty golden + produced credits => precision < 1 (hallucination penalty).
- **Multi-backend harness.** `run()` takes `backends: dict[str, EnrichmentBackend]` (named) instead
  of a single backend; `backend_from_env()` supplies a default `{"llm": ...}` when `LLM_URL` is set.
  Each album's golden is scored against every backend's `enrich_album` output.
- **Report.** New "Enrichment quality" section: backend × (precision, recall, F1) aggregate + a
  per-album breakdown; stdout summary gains the enrichment scorecard. Coverage section stays.

## Risks / Trade-offs

- **Golden authoring is judgment.** Track-attributed credits in freeform notes can be ambiguous; the
  golden encodes our reading and becomes the contract. Mitigated by conservative authoring (only
  credits the notes clearly tie to a track) and unambiguous empty goldens.
- **Matching strictness** could under-credit a correct-but-differently-phrased extraction; mitigated
  by `normalize_role` + name-overlap rather than exact equality.
