# Entities

All models are immutable pydantic v2 value objects that reject unknown fields. Multi-language text is
a `LocalizedText` (a language-label → text mapping) with a `.default` (prefers English, then Romaji)
and a `.prefer(*languages)` helper. Dates are `PartialDate` (a required year with optional month/day).

See the [API reference](../reference/models.md) for every field; this is the orientation.

## Album

`Album` carries `id`, `link`, `titles`, `catalog`, `release_date`, `classification`, cover image URLs,
`discs` (each a `Disc` of `Track`s), `credits` (each a `Credit` with a normalized `role`, the
verbatim `role_raw`, and `ArtistRef`s), `notes`, and `release_event` — an `EventRef` for the event
the album was released at, when the page links one.

```python
album = client.get_album(4)
album.titles.default            # best-available title
album.titles.prefer("Japanese") # a specific language, else default
for disc in album.discs:
    for track in disc.tracks:
        print(track.number, track.titles.default)
if album.release_event:
    print("released at", album.release_event.names.default)
```

## Other entities

- **Artist** (`get_artist`) — `id`, `link`, `names`, `type`, `notes`.
- **Product** (`get_product`) — game/franchise/etc.; `franchises` and `organizations` reference lists.
- **Organization** (`get_organization`) — company/circle/label; `id`, `link`, `names`, `type`, `notes`.
- **Event** (`get_event`) — `id`, `link`, `names`, `type`, `start_date`, `end_date`, `notes`. A
  single-day event has `end_date = None`.

## Search

`search(query)` returns `SearchResults` with an `albums` list of `AlbumSearchResult` (lightweight
hits: catalog, titles, link). Fetch a full `Album` with `get_album` using the hit's id.

## References vs entities

Lightweight `ArtistRef` / `ProductRef` / `OrgRef` / `EventRef` (just `names` + optional `id`/`link`)
point at an entity without embedding its full record — they appear inside other models (e.g. an
album's credits, or `release_event`). Fetch the full entity with the matching `get_*` method.
