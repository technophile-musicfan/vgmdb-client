## ADDED Requirements

### Requirement: Event page parser

The parsers SHALL provide a pure function `parse_event(html: str) -> Event` that extracts an `Event`
from a captured vgmdb event page using owned (clean-room) selectors. It SHALL key off
`<link rel="canonical">` (`/event/{id}`) for the id, populate localized `names`, `type`, dates, and
`notes` where present, and leave optional fields as `None` when absent. It SHALL raise
`NotAnEventPageError` (a `ParseError`) when the HTML is not an event page.

#### Scenario: Parses a captured event fixture to its golden Event

- **WHEN** `parse_event` is called with the HTML of an event fixture
- **THEN** it returns an `Event` equal to that fixture's golden `Event`

#### Scenario: Not an event page

- **WHEN** `parse_event` is called with HTML lacking an event canonical link or title
- **THEN** it raises `NotAnEventPageError`

## MODIFIED Requirements

### Requirement: Album page parser

The parsers SHALL provide a pure function `parse_album(html: str) -> Album` that extracts an `Album`
from a captured vgmdb album page using owned (clean-room) selectors. It SHALL populate id, link,
multi-language titles, catalog, release date, classification, cover images, discs with tracks,
credits, notes, and the optional `release_event` (from the `link_event` anchor in the release-date
cell) where present, and SHALL leave optional fields as `None`/empty when absent.

#### Scenario: Parses a captured album fixture to its golden Album

- **WHEN** `parse_album` is called with the HTML of an M5 album fixture
- **THEN** it returns an `Album` equal to that fixture's golden `Album`

#### Scenario: Multi-disc album

- **WHEN** `parse_album` is called on a multi-disc album page
- **THEN** the returned `Album` has one `Disc` per disc, each with its tracks in order

#### Scenario: Missing optional fields

- **WHEN** `parse_album` is called on a page lacking optional data (e.g. no notes, sparse credits,
  year-only date)
- **THEN** it still returns a valid `Album` with those fields defaulted to `None`/empty lists

#### Scenario: Album with a release event

- **WHEN** `parse_album` is called on an album page whose release-date cell has a `link_event` anchor
- **THEN** the returned `Album` has a `release_event` `EventRef` with the event's id, link, and name

#### Scenario: Album without a release event

- **WHEN** `parse_album` is called on an album page with no `link_event` anchor
- **THEN** the returned `Album` has `release_event` of `None`
