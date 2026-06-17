# Rule-based Enrichment Backend (Enrichment v2, Cycle 3) — Design

**Bead:** vgmdb-zsy.3 · **Date:** 2026-06-17 · **Workflow:** 2.

## Why

The enrichment layer has an LLM backend (Cycle 2) but no dependency-free baseline. A deterministic
rule-based backend gives a no-deps, golden-testable extractor and a baseline the Cycle 1 scorer can
rank the LLM against. The optional local-ML backend is deferred to a follow-up bead.

## Goals / Non-Goals

**Goals:**
- A `RuleBasedBackend` implementing `EnrichmentBackend` (no new deps), conservative + precision-favored.
- Cover the per-track-credit note patterns the fixtures exhibit; skip ambiguous notes.
- Measure it directly against the Cycle 1 enrichment goldens.

**Non-Goals:**
- The local-ML backend + `[ml]` pyproject extra (deferred to a new bead; the protocol is the seam).
- Changing `AlbumEnrichment`, the `EnrichmentBackend` protocol, or the LLM backend.

## Decisions

### `RuleBasedBackend` (`src/vgmdb_client/enrich/rules.py`)

A deterministic line scanner over `album.notes`.

- **`_parse_track_set(text)`** parses the range notations seen in fixtures — `1,4,5`, `1~3`,
  `01, 07`, `M-01`, `M01~12, 14~23` — into `set[int]` (`~` = inclusive range; `M`/`M-`/leading-zero
  prefixes stripped).
- **Inline parenthetical pattern:** `<Name> (<ranges>)` groups under a role context, e.g.
  `"Composition: Nobuo Uematsu (1~3)"`, `"Original compositions by: X (01); Y (02,07)"`,
  `"Arrangement by Syrufit (2,3,5,7,10)"`.
- **Block (track-context) pattern:** a line that *is* a track-range/number header (`"Tracks 1,4,5"`,
  `"M-01 - …"`, `"10. …"`, `"M01~12, 14~23"`) sets the current track set; subsequent
  `"<Role> by <Names>"` / `"<Role>: <Names>"` lines attribute to it until a blank line or the next
  header.
- `role_raw` = the matched role phrase, normalized via `normalize_role`. Names split on
  `,` / `&` / `and` / `;`. Credits are keyed by track number into an `AlbumEnrichment`.

**Precision safeguard:** a role line emits credits only when it has a track context (a preceding
range/number header) or an inline `(ranges)`. Album-level credits with no track reference (e.g.
"All Music Composed by X" — albums 4, 5012, 30000, 60000) attach to nothing and are dropped, keeping
those albums' negative goldens intact. Conservative by construction; precision favored over recall.

### Wiring

Export `RuleBasedBackend` from `enrich/__init__.py`. It is a named backend the harness can rank
alongside the LLM (`{"rule": RuleBasedBackend(), "llm": ...}`) via the Cycle 1 scorer.

## Testing

- `_parse_track_set`: each notation (comma list, `~` range, `M-`/`M0` prefixes, mixed).
- Extractor on representative note snippets (inline-parenthetical and block patterns).
- Golden-based, via the Cycle 1 scorer: assert **high recall on clean albums** (`10000`, `22000`)
  and **precision 1.0 on the empty-golden albums** (4 / 5012 / 30000 / 60000 — no hallucination).
- Deterministic, no network.

## Risks / Trade-offs

- **Format variety.** Freeform notes vary; the extractor covers the fixture patterns and deliberately
  skips ambiguous ones (lower recall is acceptable and measured by the scorer).
- **Name splitting.** Heuristic splitting can over- or under-split a multi-artist credit; the scorer's
  artist-name-overlap matching softens this, and conservative splitting limits false positives.
- **Deferred ML.** Shipping rule-based alone leaves the epic's ML promise open; tracked by a new bead.
