## Context

We have a clean-room parser (M3), an opt-in LLM enrichment overlay (B1), and a hand-authored golden
fixture dataset (M5: captured HTML + golden JSON validated against M1 models). There is no objective
measure of extraction quality. The full design is in
`docs/superpowers/vgmdb_client/2026-06-17_quality_harness_design.md`; this captures the decisions.

## Goals / Non-Goals

**Goals:**
- Run three sources over the M5 album fixtures — ours, ours+LLM, hufman — and emit a per-field
  quality report (Markdown + stdout summary).
- Score structural fields against the golden as ground truth; surface where sources disagree.
- Keep hufman entirely out of the runtime library; keep the harness out of the shipped wheel.

**Non-Goals:**
- A pass/fail quality gate (this is a measurement tool run on demand).
- Search-result comparison (album-only this iteration; structure generalizes later).
- Byte-identical hufman comparison (hufman parses live vgmdb; deferred cache-priming).

## Decisions

- **Layout.** Standalone `benchmarks/quality/` package, excluded from the wheel automatically (the
  build packages only `src/vgmdb_client`). Focused modules: `fields.py` (canonical record +
  normalizers), `adapters.py` (`from_album` / `from_golden` / `from_hufman`), `hufman_client.py`
  (httpx GET, returns dict or `None`), `compare.py` (scoring + N-way diff + coverage), `report.py`
  (Markdown + stdout), `run.py` (entry point).
- **Canonical comparison record.** Flat `field_path -> value`: album `title`, `catalog`,
  `release_date`, `classification`; per track `disc{d}.track{t}.title`. Each field has a
  normalizer for fair scoring (strip+casefold, `LocalizedText -> default`, `PartialDate -> ISO`).
- **Scoring vs golden.** Per field ∈ {match, mismatch, missing, extra}; the raw N-way diff keeps
  un-normalized values so divergences stay visible.
- **ours+LLM = coverage, not score.** The golden has no per-track-credit ground truth; ours+LLM is
  identical to ours on every scored field, so it is reported as enrichment coverage
  (tracks-with-credits / total, total credits).
- **hufman optional + over HTTP.** `HUFMAN_URL` (default `http://localhost:5000`); unreachable →
  hufman column dropped, harness continues. No hufman code vendored or imported.
- **Config via env**, mirroring B1: `HUFMAN_URL`, plus `LLM_URL`/`LLM_MODEL`/`LLM_API_KEY` through
  the existing `backend_from_env`.
- **No new runtime dep.** httpx (already runtime) covers the hufman client.

## Risks / Trade-offs

- **hufman live-fetch drift.** hufman scrapes vgmdb.net live; our fixtures are a snapshot, so the
  comparison is not byte-identical. Accepted and documented; mitigated by making hufman optional and
  treating its column as "hufman's current view." Cache-priming deferred.
- **No golden for enrichment.** ours+LLM cannot be scored vs golden; mitigated by reporting coverage
  separately and flagging "no ground truth."
- **hufman JSON shape variance.** `from_hufman` is tolerant/best-effort — missing keys map to `None`
  rather than raising — so hufman API differences degrade to "missing" rather than crashing the run.
