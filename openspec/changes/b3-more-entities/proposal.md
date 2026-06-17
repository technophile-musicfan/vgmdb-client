## Why

The client today resolves only albums and search. Albums constantly reference artists, products
(games/franchises), and organizations (companies/labels/circles), but those references are dead ends —
there is no way to fetch and validate the referenced entity. Extending the model family, parsers, and
client to these three entities makes the referenced graph navigable and is the last Beta deliverable
before V1 release polish.

## What Changes

- **Models**: add three core-subset frozen entity models — `Artist`, `Product`, `Organization` — plus
  two lightweight refs (`ProductRef`, `OrgRef`) mirroring the existing `ArtistRef`. `type` fields are
  stored verbatim; cross-refs use lightweight refs (`members`/`units` via `ArtistRef`, `franchises`
  via `ProductRef`, `organizations` via `OrgRef`). Discography/album lists and normalized type enums
  are out of scope this pass.
- **Parsers**: add `parse_artist` / `parse_product` / `parse_organization` built on the existing
  `_dom` helpers, with new error types `NotAnArtistPageError` / `NotAProductPageError` /
  `NotAnOrganizationPageError`.
- **Client**: add `get_artist` / `get_product` / `get_organization` to both `Client` and
  `AsyncClient`, with pure path builders (`/artist/{id}`, `/product/{id}`, `/org/{id}`).
- **Fixtures**: M5-style captured HTML + hand-authored golden per entity under
  `tests/fixtures/vgmdb/{artists,products,organizations}/`, manifest entries, loader functions, and
  capture-script support.

Implemented in one cycle, entity-by-entity: shared plumbing → Artist → Product → Organization.

## Capabilities

### New Capabilities
<!-- None: this extends existing capabilities. -->

### Modified Capabilities
- `models`: add `Artist`, `Product`, `Organization`, `ProductRef`, `OrgRef`.
- `parsers`: add `parse_artist`, `parse_product`, `parse_organization` and their not-a-page errors.
- `client`: add `get_artist`, `get_product`, `get_organization` (sync + async).

## Impact

- New model modules (`models/artist.py`, `product.py`, `organization.py`) + new refs in `common.py`;
  new parser modules; new error types; client path builders + methods; package `__init__` re-exports.
- New fixtures + loader functions under `tests/`; capture-script support for the new entity types.
- No new runtime dependency. No change to existing album/search behavior.
- Cross-entity refs make this a prerequisite for richer navigation; discography lists remain future
  work.
