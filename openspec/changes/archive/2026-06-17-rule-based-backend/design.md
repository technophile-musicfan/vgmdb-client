## Context

The enrich layer has an LLM backend but no dependency-free baseline to rank it against. Full design:
`docs/superpowers/vgmdb_client/2026-06-17_rule_based_backend_design.md`. Cycle 3 of the Enrichment v2
epic; consumes Cycle 1's scorer. The local-ML backend + `[ml]` extra are deferred to a follow-up bead.

## Goals / Non-Goals

**Goals:** a deterministic, no-deps `RuleBasedBackend` (conservative, precision-favored) that extracts
per-track credits from notes and is measured against the Cycle 1 goldens.

**Non-Goals:** the local-ML backend / `[ml]` extra (deferred); changing `AlbumEnrichment`, the
protocol, or the LLM backend.

## Decisions

- **`RuleBasedBackend`** (`src/vgmdb_client/enrich/rules.py`) — a line scanner over `album.notes`:
  - `_parse_track_set(text)` → `set[int]` for `1,4,5` / `1~3` / `01, 07` / `M-01` / `M01~12, 14~23`
    (`~` inclusive; `M`/`M-`/leading-zero stripped).
  - **Inline parenthetical**: `<Name> (<ranges>)` groups under a role context.
  - **Block**: a track-range/number header line (`Tracks 1,4,5`, `M-01 - …`, `10. …`,
    `M01~12, 14~23`) sets the current track set; subsequent `<Role> by/: <Names>` lines attribute to
    it until a blank line or the next header.
  - `role_raw` → `normalize_role`; names split on `,`/`&`/`and`/`;`; credits keyed by track number.
  - **Precision safeguard**: emit credits only with a track context or inline ranges — album-level
    credits with no track reference are dropped (negative goldens stay empty).
- **Wiring**: exported from `enrich/__init__.py`; a named backend for the harness.

## Risks / Trade-offs

- Freeform notes vary; the extractor covers the fixture patterns and skips ambiguous ones (lower
  recall, measured by the scorer).
- Heuristic name splitting can mis-split; softened by the scorer's artist-name-overlap matching and
  conservative splitting.
- Shipping rule-based alone leaves the epic's ML promise open — tracked by a new bead.
