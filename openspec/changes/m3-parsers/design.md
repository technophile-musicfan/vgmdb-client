## Context

M1 models and M5 golden fixtures exist; nothing yet parses vgmdb HTML into models. M3 adds
clean-room pure parsers (`parse_album`, `parse_search`) that own every selector and are validated
against the M5 fixtures. Source of truth: `docs/superpowers/vgmdb_client/2026-06-16_parsers_design.md`.
Parsers are pure (no I/O); the transport/client wiring is M4.

## Goals / Non-Goals

**Goals:**
- `parse_album(html) -> Album`, `parse_search(html) -> SearchResults` (pure), plus `ParseError`.
- A clean-room lxml extraction layer with shared DOM helpers.
- Parser output equals every M5 golden fixture.

**Non-Goals:**
- Per-track credits / freeform-notes structuring — B1 (`notes` stays a raw block).
- Artist/Product/Organization entities — B3 (credits use `ArtistRef`).
- hufman-vs-ours quality harness — B2.
- Client/transport wiring — M4.

## Decisions

**D1 — lxml.** `lxml.html` + CSS/XPath: fast, robust, powerful selectors for nested tables/spans.
*Alternatives:* selectolax (CSS-only), beautifulsoup4 (slower/weaker) — rejected.

**D2 — `parsers/` package, pure functions.** `_dom.py` (shared helpers), `album.py`, `search.py`,
`errors.py` (`ParseError`), `__init__.py`. Flow: `html → lxml tree → select → kwargs → model`
(model validation is the final guard).

**D3 — `parse_search` extracts the query from the results header.** Keeps the HTML-only signature;
the multi-hit golden `query` is corrected to the displayed `"final, fantasy"`.

**D4 — Localized-text placeholder rule (shared with goldens).** `en→English`; `ja→Japanese` only
with real CJK script; `ja-Latn→Romaji` only when it differs from English; placeholder duplicates
dropped.

**D5 — Credits verbatim + normalized.** Each row → `role_raw` (verbatim) + `role =
normalize_role(role_raw)` + `ArtistRef`s from `/artist/<id>` links; instruments → PERFORMER.

**D6 — Lenient + `ParseError` guard.** Optional fields default `None`/`[]`; raise `ParseError`
only when essential anchors are missing (no album id/title; no results container).

**D7 — Judgment-field divergences decided per-case during TDD.** Where a golden value reflects
human transcription judgment a clean-room parser won't reproduce (e.g. `33000` parenthetical-alias
merged to one; `271` venue comma-split), the parser-vs-golden tests surface each; resolve by a clean
general heuristic, or revise that golden value to the structural form with a B1 note. Goldens are
not rewritten wholesale to match the parser.

## Risks / Trade-offs

- **Exact-match demand** (every track/credit/notes-whitespace/cover URL) → small fixtures + per-
  fixture TDD; `_dom` centralizes the tricky rules.
- **Judgment-field divergence** (D7) → per-case in TDD; semantic refinement → B1.
- **New runtime dep (lxml)** → standard, binary wheels everywhere; worth the selector power.
- **vgmdb drift** → fixtures are pinned snapshots; selectors validated against them.

## Migration Plan

Additive — a new package and one runtime dependency. The only existing-data change is correcting
the multi-hit golden `query` to the displayed form. No model or transport changes.

## Open Questions

- Per-fixture judgment-field resolutions (D7) — settled during implementation as tests surface them.
