# B3 More Entities — Design

**Bead:** vgmdb-bzf.3 · **Date:** 2026-06-17 · **Workflow:** 2 (full path — schema change across models/parsers/client/fixtures)

## Purpose

Extend the M1 model family, the clean-room parsers, and the client API to three entities commonly
referenced from albums: **Artist**, **Product**, **Organization**. Acceptance:
`get_artist` / `get_product` / `get_organization` (sync + async) return validated models, fixture-tested.

## Scope & sequence

One Workflow-2 cycle, one spec, implemented as four stages, each landing green independently:

0. **Shared plumbing** — new lightweight refs (`ProductRef`, `OrgRef`), path builders, error types.
1. **Artist** (most-referenced from albums) — model → parser → client → fixture.
2. **Product** — model → parser → client → fixture.
3. **Organization** — model → parser → client → fixture.

## Decisions

### Models (core subset + lightweight refs)

New refs in `models/common.py`, mirroring the existing `ArtistRef` (`names`/`id`/`link`):
- `ProductRef` — `names: LocalizedText`, `id: int | None`, `link: str | None`
- `OrgRef` — `names: LocalizedText`, `id: int | None`, `link: str | None`

Three entity models, frozen `VgmdbModel` (`extra="forbid"`), identity/metadata + cross-refs only.
Discography/album lists are explicitly **out of scope this pass** (see Non-goals), so no `AlbumRef`
is introduced. `type` fields are stored **verbatim** as vgmdb shows them (like `Album.classification`),
no normalization.

- `Artist` (`models/artist.py`):
  - `id: int`, `link: str | None`
  - `names: LocalizedText`
  - `aliases: list[str]` — alternate names (plain strings)
  - `type: str | None` — verbatim (e.g. "Person", "Unit")
  - `birthdate: PartialDate | None`
  - `notes: str | None`
  - `members: list[ArtistRef]` — for a unit/group
  - `units: list[ArtistRef]` — groups a person belongs to
- `Product` (`models/product.py`):
  - `id: int`, `link: str | None`
  - `names: LocalizedText`
  - `type: str | None` — verbatim (e.g. "Game", "Franchise", "Animation")
  - `notes: str | None`
  - `franchises: list[ProductRef]` — parent/related products
  - `organizations: list[OrgRef]` — developers/publishers
- `Organization` (`models/organization.py`):
  - `id: int`, `link: str | None`
  - `names: LocalizedText`
  - `type: str | None` — verbatim (e.g. "Company", "Doujin Circle", "Label")
  - `notes: str | None`

All entity list fields default to empty (`Field(default_factory=list)`); optional scalars default
to `None`.

### Parsers + errors

`parsers/artist.py` / `product.py` / `organization.py` expose `parse_artist` / `parse_product` /
`parse_organization`, built on the existing `_dom` helpers (`parse_tree`, `text`, `localized_text`,
`partial_date`, `absolute_url`). Selectors are derived empirically from the captured HTML during TDD,
exactly as in M3. New error types in `parsers/errors.py`, mirroring `NotAnAlbumPageError`:
`NotAnArtistPageError`, `NotAProductPageError`, `NotAnOrganizationPageError` (each a `ParseError`).

### Client + paths

`client/_core.py` gains pure path builders: `artist_path` → `/artist/{id}`, `product_path` →
`/product/{id}`, `organization_path` → `/org/{id}`. `Client` and `AsyncClient` each gain
`get_artist(id)`, `get_product(id)`, `get_organization(id)` following the existing
`get_album` shape (`parse_*(self._transport.get(_core.*_path(id)))`). New models are re-exported from
the package `__init__`; the existing drift-guard test enforces `models.__all__ ⊆ vgmdb_client.__all__`.

### Fixtures

Mirror M5: captured HTML + hand-authored golden per entity under
`tests/fixtures/vgmdb/{artists,products,organizations}/`, recorded in `manifest.json`, with loader
functions `load_artist_fixture` / `load_product_fixture` / `load_organization_fixture` (each validates
the golden against its model on load). The capture script gains support for the new entity types. I
propose IDs already referenced from existing album fixtures (e.g. a composer credited on album 271) so
cross-entity refs resolve against data we already hold; the user runs the capture (live page + fresh
`cf_clearance`) when we reach each entity's fixture step.

### Testing

Per entity: model unit tests (construction, frozen/extra-forbid, defaults), a parser-vs-golden test
asserting full model equality (as for Album), and a client `get_*` test via a stub transport for both
sync and async. Full gate (ruff + mypy + pytest) green at the end of each stage.

## Non-Goals

- **Discography / album lists.** Parsing an entity's full list of related albums is deferred to a
  later cycle. Models carry identity, metadata, and cross-entity refs (members/units, franchises,
  organizations) but not album lists. This keeps models small and goldens authorable.
- **Normalized type enums.** `type` stays verbatim this pass; a normalized enum can be added later
  with the verbatim/normalized dual-field pattern (as `Role`/`role_raw`) if needed.
- **Search over these entities.** `search` remains album-only; entity search is future work.

## Risks / Trade-offs

- **Clean-room selectors per entity.** Each entity page has its own DOM; selectors are derived from
  captured HTML during TDD and may need iteration. Mitigated by the golden-equality tests.
- **Fixture capture depends on the user** (live page + `cf_clearance`). The cycle pauses at each
  entity's fixture step until capture is done.
- **Cross-entity ref shape variance.** `members`/`units`/`franchises`/`organizations` come from link
  blocks whose markup may differ from album credit rows; parsers extract refs best-effort and the
  golden pins the expected set.
