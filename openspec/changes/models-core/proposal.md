## Why

Every layer of vgmdb-client speaks in typed data: M3 parsers must produce something, M4 client
must return something, and M5 fixtures must assert against something. Without a shared, validated
model vocabulary there is nothing for parsers to target or for consumers to rely on. This change
defines that vocabulary for the MVP scope (albums + search).

## What Changes

- Introduce a **models layer**: pydantic v2 models that are pure (no I/O, no parsing).
- Add shared value types: `LocalizedText` (multi-language text with language-preference
  accessors), `PartialDate` (year + optional month/day, since vgmdb dates are often partial), and
  `ArtistRef` (a lightweight artist pointer).
- Add the album entity as a core subset: `Album`, `Disc`, `Track`, and `Credit` (open-ended
  role + list of `ArtistRef`).
- Add albums-only search models: `AlbumSearchResult` and `SearchResults`.
- Make all models immutable value objects (`frozen=True`) that reject unknown keys
  (`extra="forbid"`), with optional fields defaulting to `None`/empty so partial parser output is
  still valid.

Out of scope (tracked separately): HTML→model parsing (M3), track-level/freeform enrichment
(B1 deep-parse), full Artist/Product/Organization entities and non-album search categories (B3),
and album fields beyond the core subset.

## Capabilities

### New Capabilities
- `models`: The typed pydantic v2 data vocabulary for vgmdb-client — shared value types
  (`LocalizedText`, `PartialDate`, `ArtistRef`), the album entity (`Album`, `Disc`, `Track`,
  `Credit`), and albums-only search results (`AlbumSearchResult`, `SearchResults`), all immutable
  and unknown-key-rejecting.

### Modified Capabilities
<!-- None — `transport` is unaffected. -->

## Impact

- **New code:** a `src/vgmdb_client/models/` package (`common.py`, `album.py`, `search.py`,
  `__init__.py`).
- **Dependencies:** none new — `pydantic` is already a runtime dependency (added in transport).
- **Downstream:** unblocks M3 Parsers (`vgmdb-v9g.6`), M5 Fixtures (`vgmdb-v9g.5`), and later
  consumers (M4 client, B1, B3).
