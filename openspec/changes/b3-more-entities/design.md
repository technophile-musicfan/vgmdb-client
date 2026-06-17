## Context

The client resolves only albums + search; album references to artists/products/organizations are
dead ends. This change extends the M1 model family, the clean-room parsers, and the client to those
three entities. Full design:
`docs/superpowers/vgmdb_client/2026-06-17_more_entities_design.md`.

## Goals / Non-Goals

**Goals:**
- Core-subset `Artist` / `Product` / `Organization` models (identity + metadata + lightweight refs).
- `parse_artist` / `parse_product` / `parse_organization` on the existing `_dom` helpers.
- `get_artist` / `get_product` / `get_organization` on `Client` and `AsyncClient`.
- M5-style captured fixtures + golden + parser-vs-golden tests per entity.

**Non-Goals:**
- Discography / related-album lists (deferred; models carry refs, not album lists).
- Normalized `type` enums (verbatim strings this pass).
- Entity search.

## Decisions

- **Models.** Frozen `VgmdbModel` (`extra="forbid"`). New refs `ProductRef`/`OrgRef` mirror
  `ArtistRef` (`names`/`id`/`link`); no `AlbumRef` (no album lists this pass). Fields per the design
  doc: `Artist`(names, aliases, type, birthdate, notes, members, units); `Product`(names, type,
  notes, franchises, organizations); `Organization`(names, type, notes). List fields default empty,
  optional scalars default `None`.
- **Parsers.** Clean-room, selectors derived empirically from captured HTML during TDD (as M3). Each
  parser raises its `NotA*PageError` when the page is not the expected entity.
- **Client.** Pure path builders in `_core` (`/artist/{id}`, `/product/{id}`, `/org/{id}`); methods
  follow the `get_album` shape. New models re-exported from the package `__init__`.
- **Sequence.** One cycle, entity-by-entity (shared plumbing → Artist → Product → Organization), each
  a vertical slice landing green. Fixture capture is the user's step (live page + `cf_clearance`).

## Risks / Trade-offs

- Clean-room selectors differ per entity page; mitigated by golden-equality tests.
- Fixture capture depends on the user; the cycle pauses at each entity's fixture step.
- Cross-entity ref markup may differ from album credit rows; parsers extract best-effort and the
  golden pins the expected set.
