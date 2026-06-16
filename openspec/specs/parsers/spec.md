# parsers Specification

## Purpose
Clean-room pure functions that map captured vgmdb HTML to M1 models: parse_album(html) -> Album and parse_search(html) -> SearchResults. We own every selector (no third-party parser in the runtime path). Built and validated against the M5 golden fixtures; lenient on optional fields, raising ParseError on non-parseable pages.

## Requirements
### Requirement: Album page parser

The parsers SHALL provide a pure function `parse_album(html: str) -> Album` that extracts an `Album`
from a captured vgmdb album page using owned (clean-room) selectors. It SHALL populate id, link,
multi-language titles, catalog, release date, classification, cover images, discs with tracks,
credits, and notes where present, and SHALL leave optional fields as `None`/empty when absent.

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
