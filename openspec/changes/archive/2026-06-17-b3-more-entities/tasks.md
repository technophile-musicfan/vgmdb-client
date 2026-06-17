## 1. Shared plumbing

- [x] 1.1 `models/common.py`: add `ProductRef` and `OrgRef` (mirror `ArtistRef`: `names`/`id`/`link`).
  Export from `models/__init__.py`. Unit-test construction + defaults.
- [x] 1.2 `parsers/errors.py`: add `NotAnArtistPageError`, `NotAProductPageError`,
  `NotAnOrganizationPageError` (each a `ParseError`).
- [x] 1.3 `client/_core.py`: add `artist_path` (`/artist/{id}`), `product_path` (`/product/{id}`),
  `organization_path` (`/org/{id}`). Unit-test the path builders.

## 2. Artist (vertical slice)

- [x] 2.1 `models/artist.py`: `Artist` model (id, link, names, aliases, type, birthdate, notes,
  members, units). Export + drift-guard. Model unit tests (construction, frozen, extra-forbid).
- [x] 2.2 Fixture: USER captures an artist page (id referenced from album fixtures) + author golden
  under `tests/fixtures/vgmdb/artists/`; add manifest entry + `load_artist_fixture`.
- [x] 2.3 `parsers/artist.py`: `parse_artist` on `_dom` helpers; selectors from the captured HTML;
  raise `NotAnArtistPageError` for non-artist pages. Parser-vs-golden + reject tests.
- [x] 2.4 `Client.get_artist` + `AsyncClient.get_artist` via `artist_path`. Stub-transport tests
  (sync + async). Gate green.

## 3. Product (vertical slice)

- [x] 3.1 `models/product.py`: `Product` model (id, link, names, type, notes, franchises,
  organizations). Export + drift-guard. Model unit tests.
- [x] 3.2 Fixture: USER captures a product page + author golden under
  `tests/fixtures/vgmdb/products/`; manifest entry + `load_product_fixture`.
- [x] 3.3 `parsers/product.py`: `parse_product`; selectors from captured HTML; raise
  `NotAProductPageError`. Parser-vs-golden + reject tests.
- [x] 3.4 `Client.get_product` + `AsyncClient.get_product` via `product_path`. Stub-transport tests
  (sync + async). Gate green.

## 4. Organization (vertical slice)

- [x] 4.1 `models/organization.py`: `Organization` model (id, link, names, type, notes). Export +
  drift-guard. Model unit tests.
- [x] 4.2 Fixture: USER captures an organization page + author golden under
  `tests/fixtures/vgmdb/organizations/`; manifest entry + `load_organization_fixture`.
- [x] 4.3 `parsers/organization.py`: `parse_organization`; selectors from captured HTML; raise
  `NotAnOrganizationPageError`. Parser-vs-golden + reject tests.
- [x] 4.4 `Client.get_organization` + `AsyncClient.get_organization` via `organization_path`.
  Stub-transport tests (sync + async). Full gate green.
