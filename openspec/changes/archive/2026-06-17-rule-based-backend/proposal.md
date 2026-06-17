## Why

The enrichment layer has an LLM backend (Cycle 2) but no dependency-free baseline. A deterministic
rule-based backend gives a no-deps, fully golden-testable extractor and a baseline the Cycle 1 scorer
can rank the LLM against. This is Cycle 3 of the Enrichment v2 epic (vgmdb-zsy); the optional
local-ML backend is deferred to a follow-up bead.

## What Changes

- **enrich**: add a deterministic `RuleBasedBackend` implementing the `EnrichmentBackend` protocol
  (no new dependency). It scans an album's `notes` for per-track credits using:
  - track-range parsing (`1,4,5`, `1~3`, `01, 07`, `M-01`, `M01~12, 14~23`);
  - an inline-parenthetical pattern (`<Name> (<ranges>)` under a role context);
  - a block pattern (a track-range/number header line sets the current track set; subsequent
    `<Role> by/: <Names>` lines attribute to it).
  - Roles normalized via `normalize_role`; names split on `,`/`&`/`and`/`;`.
  - **Precision safeguard:** a role line emits credits only with a track context or inline ranges, so
    album-level credits with no track reference are dropped.
- Exported from `enrich/__init__.py`; usable as a named backend in the quality harness.

The optional local-ML backend and `[ml]` pyproject extra are explicitly out of scope (deferred).

## Capabilities

### New Capabilities
<!-- None: extends the existing `enrich` capability. -->

### Modified Capabilities
- `enrich`: add a deterministic, no-deps `RuleBasedBackend` for per-track-credit extraction.

## Impact

- New `src/vgmdb_client/enrich/rules.py` + export; new unit + golden-scored tests.
- No new dependency; no change to `AlbumEnrichment`, the `EnrichmentBackend` protocol, or the LLM
  backend. Tests are deterministic (no network).
