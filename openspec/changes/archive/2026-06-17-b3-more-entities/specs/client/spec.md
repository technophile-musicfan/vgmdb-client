## ADDED Requirements

### Requirement: Fetch an artist

`Client` and `AsyncClient` SHALL each provide `get_artist(artist_id)` that fetches the artist page
(path `/artist/{id}`) and returns a parsed `Artist`, reusing the shared transport and error
pass-through.

#### Scenario: get_artist returns the parsed artist

- **WHEN** `get_artist(id)` is called
- **THEN** it fetches `/artist/{id}` via the transport and returns the parsed `Artist`

### Requirement: Fetch a product

`Client` and `AsyncClient` SHALL each provide `get_product(product_id)` that fetches the product page
(path `/product/{id}`) and returns a parsed `Product`.

#### Scenario: get_product returns the parsed product

- **WHEN** `get_product(id)` is called
- **THEN** it fetches `/product/{id}` via the transport and returns the parsed `Product`

### Requirement: Fetch an organization

`Client` and `AsyncClient` SHALL each provide `get_organization(org_id)` that fetches the
organization page (path `/org/{id}`) and returns a parsed `Organization`.

#### Scenario: get_organization returns the parsed organization

- **WHEN** `get_organization(id)` is called
- **THEN** it fetches `/org/{id}` via the transport and returns the parsed `Organization`
