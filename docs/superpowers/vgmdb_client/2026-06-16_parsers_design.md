# M3 Parsers — Feature Design

**Date:** 2026-06-16
**Status:** Design (Workflow 2, step 1)
**Epic:** `vgmdb-v9g.6` (M3 Parsers) — parent `vgmdb-v9g` (MVP)
**Major scope:** `vgmdb_client`
**Vision:** `docs/superpowers/2026-06-14_vgmdb_client.md`
**Depends on:** M1 Models (merged), M5 Fixtures (merged), M1.x Credit role normalization (merged)

## Purpose

Clean-room pure functions that turn captured vgmdb HTML into M1 models:
`parse_album(html) -> Album` and `parse_search(html) -> SearchResults`. We own every selector —
no third-party (hufman) code in the runtime path. The M5 golden fixtures are the TDD ground truth.

## Scope

**In scope**
- `parse_album(html: str) -> Album` and `parse_search(html: str) -> SearchResults` (pure, no I/O).
- A clean-room extraction layer using **lxml** (new runtime dependency).
- Validation against all M5 golden fixtures (parser output == golden).
- Edge cases: multi-disc, multi-language titles, partial dates, sparse/rich credits, missing
  optional fields, drama-CD/no-track-titles, year-only/year-month/full dates.

**Out of scope (tracked elsewhere)**
- Per-track credits / freeform-notes structuring → **B1** (`vgmdb-bzf.1`); `notes` stays a raw block.
- Artist/Product/Organization entities → **B3** (`vgmdb-bzf.3`); credits use `ArtistRef`.
- The hufman-vs-ours quality harness → **B2** (`vgmdb-bzf.2`).
- The client/transport wiring that calls these parsers → **M4** (`vgmdb-v9g.7`).

## Decisions

**D1 — lxml.** `lxml.html` with CSS (`cssselect`) and/or XPath. Fast, robust on real-world HTML,
powerful selectors for vgmdb's nested tables/spans. *Alternatives:* selectolax (CSS-only, less
ubiquitous), beautifulsoup4 (friendliest but slower/weaker selectors) — rejected for selector power.

**D2 — `parsers/` package, pure functions.** New `src/vgmdb_client/parsers/`:
- `_dom.py` — shared helpers: parse tree, whitespace-normalized text, **localized-text from
  language spans**, partial-date-from-text, relative→absolute URL.
- `album.py` — `parse_album`.
- `search.py` — `parse_search`.
- `errors.py` — `ParseError(VgmdbClientError)`.
- `__init__.py` — exports `parse_album`, `parse_search`, `ParseError`.
Each function: `html → lxml tree → select → build kwargs → construct model` (model validation is
the final guard).

**D3 — `parse_search` extracts the query from the page.** The results header echoes the query
(e.g. `"final, fantasy"`); `parse_search(html)` reads it (keeps the epic's HTML-only signature).
Consequence: the multi-hit golden `query` is corrected to the displayed form `"final, fantasy"`
during implementation. *Alternative:* pass query as a param — rejected (deviates from the signature
and decouples query from the page).

**D4 — Localized-text placeholder rule (shared with the goldens).** From the title/track language
spans: `en → English`; `ja → Japanese` only when the span holds real CJK script; `ja-Latn → Romaji`
only when it differs from the English text. Identical placeholder duplicates are dropped — the exact
rule already encoded in the M5 goldens.

**D5 — Credits: verbatim + normalized.** Each credit row yields `role_raw` (the verbatim label) and
`role = normalize_role(role_raw)` (the merged M1.x helper); artists are `ArtistRef`s built from
`/artist/<id>` links (id/link absolute, names per language span), instruments map to PERFORMER via
`normalize_role`.

**D6 — Lenient parsing with a `ParseError` guard.** Optional fields default to `None`/`[]` when
absent (matches the M1 partial-data models). Raise a typed `ParseError` only when the essential
anchors are missing — no album id/title for `parse_album`, no results container for `parse_search`
(e.g. a slipped-through Cloudflare/404 page). *Alternatives:* strict (brittle against genuinely
optional fields) and fully-lenient (garbage/invalid models) — both rejected.

**D7 — Judgment-field divergences decided per-case during TDD.** A few golden values reflect human
transcription judgment a clean-room parser won't reproduce (e.g. `33000` `Syrufit (hiro.na)` merged
to one artist where the HTML has two links; `271` venue comma-split). The parser-vs-golden tests
surface each; for each, either encode a clean general heuristic, or revise that golden value to the
structural form and file a B1 note for the semantic refinement. The goldens are not rewritten
wholesale to match the parser (that would destroy their independence).

## Data flow

```
html ─▶ lxml.html.fromstring ─▶ select fields (CSS/XPath via _dom helpers)
     ─▶ build model kwargs ─▶ Album(...) / SearchResults(...)   [validation = final guard]
     (ParseError if essential anchors missing)
```

## Album field extraction (selectors own the mapping)

- `id`, `link`: canonical `<link rel="canonical">` / `/album/<id>`.
- `titles`: `<h1>` language spans → localized-text rule (D4).
- `catalog`, `classification`, `release_date`: info-box label→value rows; date text → `PartialDate.parse`.
- `cover_full` (medium-media URL), `cover_small` (thumb-media URL).
- `discs[]`: each disc's tracklist table → `Disc{number, name, tracks}`; `tracks[]` →
  `Track{titles (per-language), number, length}`.
- `credits[]`: each role row → `Credit{role, role_raw, artists}` (D5).
- `notes`: the notes block as raw text (`<br>` → `\n`, entities decoded).

## Search field extraction

- `query`: from the results header (D3).
- `albums[]`: each result row → `AlbumSearchResult{id, link, titles, catalog, release_date}`.
- Parser returns every result row present on the page.

## Testing

- **Parser-vs-golden** against the M5 fixtures via `tests/support/fixtures.py`:
  - Album: `parse_album(html) == golden Album` for every fixture (frozen-model value equality).
  - Search: `near-empty` → full equality (0 results); `multi-hit` (manifest `golden_scope:
    "first-10"`) → `parsed.albums[:10] == golden.albums` and `parsed.query == golden.query`.
- **Unit tests** for `_dom` helpers (localized-text rule, partial-date parse, URL absolutize),
  independent of fixtures.
- **TDD order:** `_dom` + `271` (single-disc/english-only/full-date) first, then `4` (multi-disc),
  `5012`/`45000` (multi-language), `18536` (year-only), `30000` (drama/no-titles), remaining albums,
  then `parse_search` (near-empty → multi-hit).
- `ruff`, `mypy`, full suite green.

## Risks / Trade-offs

- **Exact-match demand.** The parser must reproduce each golden field-for-field (tracks, credits,
  notes whitespace, cover URLs). Mitigation: the fixtures are small and the TDD loop is per-fixture;
  `_dom` centralizes the tricky rules (language spans, dates, URLs).
- **Judgment-field divergence** (D7) → resolved per-case in TDD; semantic refinements deferred to B1.
- **vgmdb structure drift** → fixtures are pinned snapshots; selectors are validated against them.
- **New runtime dep (lxml)** → standard, binary wheels on all target platforms; worth the selector power.

## Acceptance criteria (from the epic)

- `parse_album(html) -> Album` and `parse_search(html) -> SearchResults` as pure functions.
- Pass against all seed fixtures.
- Handle multi-disc and missing-field edge cases.

## Open questions / deferrals

- Exact per-fixture judgment-field resolutions (D7) — settled during implementation as the
  parser-vs-golden tests surface them; semantic refinements (alias collapse, venue splitting) → B1.
