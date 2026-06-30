# parsers Specification

## Purpose
Clean-room pure functions that map captured vgmdb HTML to M1 models: parse_album(html) -> Album and parse_search(html) -> SearchResults. We own every selector (no third-party parser in the runtime path). Built and validated against the M5 golden fixtures; lenient on optional fields, raising ParseError on non-parseable pages.
## Requirements
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

### Requirement: Search results parser

The parsers SHALL provide a pure function `parse_search(html: str) -> SearchResults` that extracts
the query (as displayed in the results header) and every album result row present on the page into
`AlbumSearchResult` entries.

#### Scenario: Parses a captured search fixture

- **WHEN** `parse_search` is called with the HTML of the multi-hit search fixture
- **THEN** the returned `query` equals the displayed query and the first results equal the golden's
  recorded results (the golden is a first-N sample)

#### Scenario: Empty results

- **WHEN** `parse_search` is called on a zero-results page
- **THEN** it returns a `SearchResults` with the displayed query and an empty `albums` list

### Requirement: Normalized credit extraction

`parse_album` SHALL record each credit's verbatim source label as `role_raw` and its normalized
`role` via `normalize_role(role_raw)`, with artists as `ArtistRef` built from the `/artist/<id>`
links present in the credit row.

#### Scenario: Verbatim and normalized role

- **WHEN** a credit row labelled "Original Music Composed by" is parsed
- **THEN** the resulting `Credit` has `role_raw` "Original Music Composed by" and `role`
  `Role.COMPOSER`

### Requirement: Multi-language title extraction

`parse_album` and `parse_search` SHALL build `LocalizedText` from the page's language spans,
recording a Japanese entry only when the span contains real Japanese script and a Romaji entry only
when it differs from the English text (placeholder duplicates are dropped).

#### Scenario: English-only title with placeholder spans

- **WHEN** a title's `ja`/`ja-Latn` spans merely duplicate the English Latin text
- **THEN** the parsed `titles` contains only the English entry

#### Scenario: Genuine multi-language title

- **WHEN** a title has a `ja` span with Japanese script
- **THEN** the parsed `titles` contains both the English and the Japanese entries

### Requirement: Parse error on non-parseable pages

The parsers SHALL raise a typed `ParseError` when a page lacks the essential anchors of the expected
page type (no album id/title for `parse_album`; no results container for `parse_search`), rather
than returning a degenerate or invalid model.

#### Scenario: Wrong page raises ParseError

- **WHEN** `parse_album` is called with HTML that is not an album page (e.g. a Cloudflare challenge
  or 404 page)
- **THEN** it raises `ParseError`

### Requirement: Artist page parser

The parsers SHALL provide `parse_artist(html)` that returns a validated `Artist` from a captured
vgmdb artist page, extracting names, aliases, verbatim type, birthdate, notes, and member/unit refs.
When the HTML is not an artist page it SHALL raise `NotAnArtistPageError` (a `ParseError`).

#### Scenario: Parse an artist page into an Artist

- **WHEN** `parse_artist` is given a captured artist page
- **THEN** it returns an `Artist` equal to the page's golden model

#### Scenario: Reject a non-artist page

- **WHEN** `parse_artist` is given HTML that is not an artist page
- **THEN** it raises `NotAnArtistPageError`

### Requirement: Product page parser

The parsers SHALL provide `parse_product(html)` that returns a validated `Product` from a captured
vgmdb product page, extracting names, verbatim type, notes, franchise refs, and organization refs.
When the HTML is not a product page it SHALL raise `NotAProductPageError` (a `ParseError`).

#### Scenario: Parse a product page into a Product

- **WHEN** `parse_product` is given a captured product page
- **THEN** it returns a `Product` equal to the page's golden model

#### Scenario: Reject a non-product page

- **WHEN** `parse_product` is given HTML that is not a product page
- **THEN** it raises `NotAProductPageError`

### Requirement: Organization page parser

The parsers SHALL provide `parse_organization(html)` that returns a validated `Organization` from a
captured vgmdb organization page, extracting names, verbatim type, and notes. When the HTML is not an
organization page it SHALL raise `NotAnOrganizationPageError` (a `ParseError`).

#### Scenario: Parse an organization page into an Organization

- **WHEN** `parse_organization` is given a captured organization page
- **THEN** it returns an `Organization` equal to the page's golden model

#### Scenario: Reject a non-organization page

- **WHEN** `parse_organization` is given HTML that is not an organization page
- **THEN** it raises `NotAnOrganizationPageError`

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
