## Why

vgmdb.net's standalone entity pages are `/album/`, `/artist/`, `/org/`, `/product/`, `/event/`, and
`/search`. Every type except `/event/` is implemented. There is no `/release/` URL on vgmdb; the
concrete "release" data on an album page is the **event the album was released at** (an
`<a class="link_event" href="/event/...">` anchor by the release date). V1b (epic `vgmdb-0e5.2`)
completes entity coverage by adding the `Event` entity and linking albums to their release event —
the last feature gating the V1 release alongside V1c.

## What Changes

- Add an `Event` model (core subset: `id`, `link`, `names`, `type`, `start_date`, `end_date`,
  `notes`), composed like the other entities. Released-album / related lists are out of scope.
- Add an `EventRef` lightweight reference (`names`, optional `id`/`link`), mirroring `ArtistRef`/
  `OrgRef`/`ProductRef`.
- Add `parse_event(html) -> Event`, a clean-room parser keyed off `<link rel="canonical">`, raising a
  new `NotAnEventPageError`.
- Add `get_event(event_id)` to `Client` and `AsyncClient`, with `event_path` in the shared `_core`.
- **Extend `Album`**: add `release_event: EventRef | None` (default `None`), parsed from the
  `link_event` anchor in the release-date cell. Purely additive — existing album fields and goldens
  are unchanged.
- Re-export `Event` and `EventRef` at the top level (entity models are re-exported).

## Capabilities

### New Capabilities
(none — the Event entity fits the existing models/parsers/client capabilities, like the B3 entities)

### Modified Capabilities
- `models`: add the `Event` model and the `EventRef` reference; add the optional `release_event` field to the `Album` model.
- `parsers`: add the `Event` page parser (`parse_event`) and `NotAnEventPageError`; the album parser now also populates `release_event`.
- `client`: add `get_event` (sync + async) and the `/event/{id}` path.

## Impact

- **New code:** `src/vgmdb_client/models/event.py`, `src/vgmdb_client/parsers/event.py`.
- **Modified code:** `models/common.py` (`EventRef`), `models/album.py` (`release_event`),
  `models/__init__.py` + top-level `__init__.py` (exports), `parsers/album.py` (release-event anchor),
  `parsers/errors.py` (`NotAnEventPageError`), `client/sync_client.py`, `client/async_client.py`,
  `client/_core.py`.
- **Fixtures:** a captured `/event/` page + golden JSON must be added; album fixture 33000 (which has
  a `link_event`) gains a populated `release_event` in its golden.
- **Dependencies:** none added.
- **Public API:** `Event`, `EventRef` re-exported from `vgmdb_client`.
