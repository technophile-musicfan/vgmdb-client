## ADDED Requirements

### Requirement: Fetch an event

`Client` and `AsyncClient` SHALL each provide `get_event(event_id)` that fetches the event page
(path `/event/{id}`) and returns a parsed `Event`, reusing the shared transport and error
pass-through.

#### Scenario: get_event returns the parsed event

- **WHEN** `get_event(id)` is called
- **THEN** it fetches `/event/{id}` via the transport and returns the parsed `Event`

#### Scenario: sync and async agree

- **WHEN** `Client` and `AsyncClient` are given the same event page HTML for the same request
- **THEN** they return equal `Event` models
