## ADDED Requirements

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
