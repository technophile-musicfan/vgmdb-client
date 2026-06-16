## Why

Every layer above the transport needs typed data, and the M1 models + M5 golden fixtures define
exactly what a correct parse must produce — but nothing yet turns captured vgmdb HTML into those
models. M3 adds the clean-room parsers (we own every selector; no hufman in the runtime path),
validated against the M5 fixtures. It unblocks the M4 client and the B1/B2/B3 beta work.

## What Changes

- Add a **`parsers` package** (`src/vgmdb_client/parsers/`) of pure functions:
  - `parse_album(html: str) -> Album`
  - `parse_search(html: str) -> SearchResults`
  - `ParseError(VgmdbClientError)` raised when a page lacks the essential anchors (not an
    album/search page — e.g. a slipped-through Cloudflare/404 page).
- Add **lxml** as a **runtime** dependency (the HTML parsing backend).
- Extraction rules (clean-room, owned selectors): multi-language titles via the placeholder rule
  (en→English; ja→Japanese only if real CJK; ja-Latn→Romaji only if it differs from English);
  partial dates (`PartialDate.parse`); credits as `role_raw` + `role = normalize_role(role_raw)`
  + `ArtistRef`; cover URLs; multi-disc tracklists; raw `notes`. `parse_search` reads the query
  from the results header and returns every result row.
- Lenient parsing: optional fields default to `None`/`[]`; only essential-anchor absence raises.

Out of scope (tracked separately): per-track credits / freeform-notes structuring → B1
(`vgmdb-bzf.1`); Artist/Product/Organization entities → B3 (`vgmdb-bzf.3`); the hufman-vs-ours
quality harness → B2 (`vgmdb-bzf.2`); the client/transport wiring that calls the parsers → M4
(`vgmdb-v9g.7`).

## Capabilities

### New Capabilities
- `parsers`: Clean-room pure functions mapping vgmdb HTML to M1 models — `parse_album` and
  `parse_search` plus a `ParseError`, with shared DOM helpers (localized-text placeholder rule,
  partial-date, URL absolutization). Validated against the M5 golden fixtures.

### Modified Capabilities
<!-- None — `models`, `transport`, and `fixtures` are consumed unchanged. -->

## Impact

- **New code:** `src/vgmdb_client/parsers/` (`_dom.py`, `album.py`, `search.py`, `errors.py`,
  `__init__.py`).
- **Dependencies:** adds **lxml** (runtime). Consumes M1 models + `normalize_role` unchanged.
- **Fixtures:** one golden correction — multi-hit search `query` → the page's displayed
  `"final, fantasy"` (the form `parse_search` extracts).
- **Downstream:** unblocks M4 client (`vgmdb-v9g.7`), B1/B2/B3.
