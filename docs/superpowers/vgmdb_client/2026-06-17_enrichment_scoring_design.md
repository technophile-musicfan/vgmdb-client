# Enrichment Goldens + Scoring (Enrichment v2, Cycle 1) — Design

**Epic context:** follow-up on B1 (enrich) + B2 (harness). **Date:** 2026-06-17 · **Workflow:** 2.

## Why

B2's harness reports the ours+LLM column as *coverage only* ("N tracks gained credits") because we
never authored per-track-credit ground truth. So today we cannot **score** or **compare** enrichment
backends — exactly what's needed to judge LLM vs prompt vs the future lightweight/ML backends. This
cycle adds the ground truth and the scoring, and makes the harness rank multiple named backends.

## Roadmap (this is Cycle 1 of 3)

1. **Cycle 1 — Enrichment goldens + scoring (this doc):** the measurement enabler.
2. **Cycle 2 — LLM backend v2:** injectable system + user prompt; selectable `json_object`
   / `json_schema` / `tool` output modes; response-model validation + one retry.
3. **Cycle 3 — Lightweight backends:** a deterministic rule-based extractor (no deps, always
   available) and an optional local-ML backend behind a `[ml]` pyproject extra; both ranked via the
   Cycle 1 scorer.

## Goals / Non-Goals

**Goals:**
- Hand-authored per-track-credit goldens for the album fixtures, validated against `AlbumEnrichment`.
- A credit-matching scorer producing precision / recall / F1 per backend.
- A harness that runs **multiple named backends** and reports enrichment quality side by side.

**Non-Goals:**
- New backends (Cycles 2–3). Cycle 1 is exercised with stub backends; no network in CI.
- Changing `AlbumEnrichment` or the `EnrichmentBackend` Protocol.
- Live LLM calls in tests.

## Decisions

### Enrichment goldens

- New dir `tests/fixtures/vgmdb/enrichment/<album_id>.json`, each a serialized `AlbumEnrichment`
  (`album_id` + `track_credits` keyed by track number), hand-authored from the album's freeform
  `notes` and validated against the model on load (fails loudly on schema drift, like M5 goldens).
- **Every** album fixture gets a golden. A handful carry the real per-track credits extracted from
  notes (e.g. 271 "Performed by …", and others among 22000/33000/45000/90000/18536 confirmed by
  inspection). The rest are **empty** (`{"album_id": N, "track_credits": {}}`) — negative ground
  truth so a backend that invents credits is penalized on precision.
- Loaders in `tests/support/fixtures.py`: `load_enrichment_golden(album_id) -> AlbumEnrichment` and
  `iter_enrichment_goldens() -> Iterator[int]`. No new HTML capture (notes already captured in M5).

### Credit-matching scorer (`benchmarks/quality/enrichment.py`)

- A credit's identity for matching: `(track_number, normalized Role, frozenset of casefolded artist
  names)`. Matching rule: same track number **and** same `Role` **and** non-empty artist-name overlap
  (casefolded), so role/name wording differences don't over-penalize.
- Per album and aggregate: **precision** = matched / produced, **recall** = matched / golden,
  **F1** = harmonic mean. Recall rewards extracting real credits; precision (via empty goldens)
  penalizes hallucination. A backend producing nothing on an empty golden scores perfectly there.
- Pure functions over two `AlbumEnrichment` values; no I/O. Reuses `vgmdb_client.models` types.

### Multi-backend harness

- Extend `benchmarks/quality/run.py`'s `run()` to accept a **mapping of named backends**
  (`dict[str, EnrichmentBackend]`) instead of a single `backend`, so the report ranks them together
  (the "compare the LLMs / the prompt / the lightweight" ask). `backend_from_env()` still supplies a
  default `{"llm": ...}` when `LLM_URL` is set; with none, the enrichment section reports "no
  backends".
- For each album the runner loads its enrichment golden and scores each backend's `enrich_album`
  output against it.

### Report (`benchmarks/quality/report.py`)

- New **"Enrichment quality"** section: a table of backend × (precision, recall, F1) aggregate, plus
  a per-album breakdown. The existing coverage section stays (it's still useful when no golden or no
  backend). Stdout summary gains the enrichment scorecard.

## Testing

- Golden load/validate (round-trips through `AlbumEnrichment`).
- Scorer unit tests on synthetic `AlbumEnrichment` pairs: exact match, partial recall, hallucination
  against an empty golden (precision < 1), role mismatch, artist-name-overlap matching, F1 math, and
  the empty-vs-empty perfect case.
- Smoke test: run the harness over the fixtures with **stub backends** (one perfect, one empty),
  asserting the enrichment scorecard appears and the perfect stub scores recall 1.0 on a populated
  album. No network, no Docker.

## Risks / Trade-offs

- **Golden authoring is judgment work.** Track-attributed credits in freeform notes can be
  ambiguous; goldens encode our reading and become the contract (a backend disagreeing is "wrong" by
  definition). Mitigated by conservative authoring (only credits the notes clearly attribute to a
  track) and by empty goldens being unambiguous.
- **Matching strictness.** Requiring same track + role + name-overlap may under-credit a backend that
  is right but phrases a role differently; `normalize_role` already collapses role wording, and
  name-overlap (not equality) softens artist differences.
