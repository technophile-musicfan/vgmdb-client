# V1b Remaining entities — Design

**Date:** 2026-06-18
**Status:** Design (Workflow 2, brainstorm)
**Major scope:** `vgmdb_client`
**Epic:** `vgmdb-0e5.2` (V1b Remaining entities), under `vgmdb-0e5` (V1: complete & polished)
**Builds on:** M1 Models (`vgmdb-v9g.3`), M3 Parsers (`vgmdb-v9g.6`), M4 Client (`vgmdb-v9g.7`), B3 entities (`vgmdb-bzf.3`)

## Problem

vgmdb.net's standalone entity pages are `/album/`, `/artist/`, `/org/`, `/product/`, `/event/`, and
`/search`. Of these, `/event/` is the one type not yet implemented. There is no `/release/` URL on
vgmdb; the concrete "release" data on an album page is the **event the album was released at** — an
`<a class="link_event" href="/event/...">` anchor in the release-date row (present e.g. in album
33000). V1b completes the entity coverage by adding the `Event` entity and linking albums to their
release event.

## Scope decisions (brainstorm)

| Axis | Decision |
|------|----------|
| Entities | Add the `Event` entity (`/event/{id}`). No `/release/` entity exists. |
| Album extension | Add `release_event: EventRef \| None` (the `link_event` anchor). NOT a full editions/printings/reprints list — that structure is not present in the page data ("reprint" appears in zero fixtures; "edition" is mostly title/classification text). |
| Event richness | Core subset only (like `Organization`/`Product`). Released-album / related lists out of scope. |
| Search | Not extended — events are not added to search results this cycle. |

## Approach (chosen: A — mirror the established entity pattern)

Every shipped entity follows the same shape: a frozen `VgmdbModel` (id, link, localized `names`,
verbatim `type`, `notes`), a clean-room parser keyed off `<link rel="canonical">` with a dedicated
`NotA<X>PageError`, sync+async `get_*` client methods over a shared `_core` path builder, and a
captured HTML fixture + golden JSON. `Event` mirrors this exactly. Rejected: B (richer Event with
released-album list + search — inconsistent with the deliberate core-subset precedent) and C (id/link/
names only — too thin to be useful).

## Components

### Shared ref — `models/common.py`
```python
class EventRef(VgmdbModel):
    names: LocalizedText
    id: int | None = None
    link: str | None = None
```
Identical shape to `ArtistRef` / `OrgRef` / `ProductRef`.

### `Event` model — `models/event.py`
```python
class Event(VgmdbModel):
    id: int
    link: str | None = None
    names: LocalizedText
    type: str | None = None              # verbatim if the page shows one
    start_date: PartialDate | None = None
    end_date: PartialDate | None = None  # None when single-day or not shown
    notes: str | None = None
```
The exact field set is confirmed against the captured fixture during implementation; fields with no
corresponding page data stay at their defaults rather than being invented.

### `parsers/event.py`
`parse_event(html) -> Event`, clean-room owned selectors:
- id from `//link[@rel="canonical"]/@href` → `/event/(\d+)`; raise `NotAnEventPageError` if absent.
- `names` from the `<h1>` title spans, reusing `_dom.localized_text` + the `_leading_group` idiom;
  raise `NotAnEventPageError` if empty.
- dates via `_dom.partial_date`.
- New `NotAnEventPageError(ParseError)` in `parsers/errors.py`.

### Album extension — `models/album.py` + `parsers/album.py`
- Add `release_event: EventRef | None = None` to `Album` (purely additive; default `None` keeps every
  existing album fixture/golden valid).
- In `parse_album`, read the `a.link_event` anchor within the release-date value cell: `href` →
  `/event/{id}`, name from the anchor's `title` (strip a leading "Released at ") or its text. Absent →
  `None`.

### Clients — `client/sync_client.py`, `async_client.py`, `_core.py`
- `event_path(event_id) -> "/event/{id}"` in `_core`.
- `get_event(event_id) -> Event` on `Client` and `async get_event` on `AsyncClient`, mirroring the
  other `get_*` methods. Transport/parser errors pass through unchanged.

### Public API — `vgmdb_client/__init__.py` and `models/__init__.py`
Re-export `Event` and `EventRef` at the top level (entity models are re-exported, unlike the
namespaced `auth`/`enrich` packages).

## Error handling

- Non-event page → `NotAnEventPageError` (a `ParseError`), consistent with the other parsers.
- Client `get_event` adds no error semantics: transport errors and `ParseError` propagate unchanged.
- Album `release_event` is best-effort: a missing/malformed `link_event` yields `None`, never raises.

## Testing

Offline, fixture-based, no live network in CI:
- Capture ≥1 real `/event/` HTML fixture + golden JSON (must be fetched live, as with every other
  entity — see Dependencies).
- `parse_event` against the golden; `NotAnEventPageError` on a non-event page.
- `get_event` sync + async parity via a stub transport (mirrors existing client tests).
- Album: `release_event` populates for the event-linked fixture (33000) and is `None` for albums
  without a `link_event`. Re-capture/confirm 33000 carries the anchor.

## Dependencies / sequencing

- **Fixture capture is a prerequisite** for the parser/client tests: the maintainer must capture a
  real `/event/` page (and confirm an album fixture with a `link_event`, e.g. 33000). The author
  cannot fetch live (Cloudflare + token). Plan should order fixture capture before parser tests.

## Ceremony (CLAUDE.md scaling)

This change spans models + parsers + client AND modifies the shipped Album parser → **multi-subsystem**.
It takes the **fuller** Workflow-2 path: a separate `/superpowers:writing-plans` plan doc and per-unit
beads, with implementation via subagent-driven development. The non-negotiable
`/opsx:verify` → `/opsx:archive` → `/code-review` gates still apply.

## Out of scope / deferred

- A `/release/`-style entity (does not exist on vgmdb).
- A structured album editions/printings/reprints list (not present in page data).
- Released-album / related-entity lists on the Event page (consistent with Org/Product core subset).
- Events in search results.
