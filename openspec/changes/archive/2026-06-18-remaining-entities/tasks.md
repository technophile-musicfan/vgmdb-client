## 1. Fixtures (prerequisite)

- [x] 1.1 Capture a real `/event/{id}` page HTML into `tests/fixtures/vgmdb/events/<id>.html` and author its golden `<id>.json`
- [x] 1.2 Confirm album fixture 33000 carries the `link_event` anchor; update its golden to include the expected `release_event`
- [x] 1.3 Add an `events` loader to `tests/support/fixtures` (mirror `load_album_fixture`/`load_product_fixture`)

## 2. Models

- [x] 2.1 Add `EventRef` to `models/common.py` (names + optional id/link, mirroring `OrgRef`)
- [x] 2.2 Add `models/event.py` `Event(id, link, names, type, start_date, end_date, notes)` as a frozen `VgmdbModel`
- [x] 2.3 Add `release_event: EventRef | None = None` to `Album` in `models/album.py`
- [x] 2.4 Re-export `Event` and `EventRef` from `models/__init__.py` and top-level `vgmdb_client/__init__.py`
- [x] 2.5 Unit tests: `Event` construction (full + partial), `EventRef`, `Album` with/without `release_event`, frozen/unknown-key rejection

## 3. Parsers

- [x] 3.1 Add `NotAnEventPageError(ParseError)` to `parsers/errors.py`
- [x] 3.2 Add `parsers/event.py` `parse_event(html) -> Event`: id from canonical `/event/(\d+)`, localized `names` from `<h1>` (reuse `_dom` + `_leading_group`), dates via `_dom.partial_date`; raise `NotAnEventPageError` when not an event page
- [x] 3.3 Extend `parsers/album.py` to populate `release_event` from the `link_event` anchor in the release-date cell (id from `/event/{id}`, name from the anchor `title` minus a leading "Released at ", else its text); absent → `None`
- [x] 3.4 Unit tests: `parse_event` against the golden + `NotAnEventPageError` on a non-event page; album `release_event` populated for 33000 and `None` for an album without the anchor; existing album tests stay green

## 4. Client

- [x] 4.1 Add `event_path(event_id) -> "/event/{id}"` to `client/_core.py`
- [x] 4.2 Add `get_event` to `Client` and `async get_event` to `AsyncClient`
- [x] 4.3 Unit tests: `get_event` sync + async parity via stub transport; error pass-through

## 5. Verification

- [x] 5.1 Run ruff + mypy + full test suite green; confirm no new runtime dependency
- [x] 5.2 Confirm `from vgmdb_client import Event, EventRef` works and the public-API surface tests pass
