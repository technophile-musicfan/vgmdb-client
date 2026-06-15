# M1 Models — Feature Design

**Date:** 2026-06-15
**Status:** Design (Workflow 2, step 1)
**Epic:** `vgmdb-v9g.3` (M1 Models) — parent `vgmdb-v9g` (MVP)
**Major scope:** `vgmdb_client`
**Vision:** `docs/superpowers/2026-06-14_vgmdb_client.md`

## Purpose

M1 is the **pydantic v2 model layer** — the typed vocabulary every other layer speaks. M3
parsers construct these models from vgmdb HTML; M4 client and M5 fixtures consume them. The
layer is pure: no I/O, no parsing, no network.

One sentence: *the typed shapes for an album, its tracklist and credits, and album search
results.*

## Scope

**In scope**
- Shared value types: `LocalizedText`, `PartialDate`, `ArtistRef`.
- Album entity: `Album`, `Disc`, `Track`, `Credit` (core subset of album fields).
- Search: `AlbumSearchResult`, `SearchResults` (albums only).
- Validation conventions (frozen, `extra="forbid"`, optional defaults).

**Out of scope (tracked elsewhere)**
- HTML → model parsing → **M3** (`vgmdb-v9g.6`).
- Track-level credits / freeform enrichment → **B1 deep-parse** (`vgmdb-bzf.1`).
- Full `Artist` / `Product` / `Organization` entities and non-album search categories → **B3**
  (`vgmdb-bzf.3`).
- Album fields beyond the core subset (products, related albums, stores, reviews, ratings/votes,
  websites, distributor, barcode) → later tiers.

## Module layout

```
src/vgmdb_client/models/
  __init__.py     # re-exports the public model surface
  common.py       # LocalizedText, PartialDate, ArtistRef  (shared value types)
  album.py        # Track, Disc, Credit, Album
  search.py       # AlbumSearchResult, SearchResults
```

Small focused files, one concern each.

## Value types (`common.py`)

### LocalizedText

vgmdb titles, names, and track titles are multi-language (e.g. `{"English": …, "Japanese": …,
"Romaji": …}`). `LocalizedText` is a `RootModel[dict[str, str]]` wrapping `language → text`,
centralizing the "pick a language" logic:

- `prefer(*langs) -> str | None` — first available among the requested languages, else the
  `default` fallback.
- `default -> str | None` — best available, preferring English then Romaji then any remaining
  entry; `None` if empty.
- `all -> dict[str, str]` — the raw mapping.
- `__str__` returns `default or ""`.
- Tolerates an empty mapping (some entities lack names).

### PartialDate

vgmdb release dates are frequently partial (year-only or year-month):

- Fields: `year: int` (required), `month: int | None = None`, `day: int | None = None`.
- Validation: `1 ≤ month ≤ 12`; `1 ≤ day ≤ 31`; `day` requires `month` (a day without a month is
  rejected).
- `precision -> "year" | "month" | "day"`.
- `__str__` -> `"YYYY"`, `"YYYY-MM"`, or `"YYYY-MM-DD"` by precision (zero-padded).
- `PartialDate.parse(value: str) -> PartialDate | None` — classmethod handling the three shapes;
  returns `None` on unparseable input. Lives here so M3 and tests share one implementation.

### ArtistRef

A lightweight pointer to an artist, distinct from the full `Artist` entity (Beta B3):

- `names: LocalizedText`, `id: int | None = None`, `link: str | None = None`.

## Entity models (`album.py`)

### Track
- `titles: LocalizedText`
- `number: int | None = None`
- `length: str | None = None` — raw `"mm:ss"` as shown for MVP. A parsed duration (e.g.
  `timedelta`) is a deferrable enhancement, not required now.

### Disc
- `number: int | None = None`
- `name: str | None = None`
- `tracks: list[Track] = []`

### Credit
- `role: str` — open-ended (Composer, Arranger, Performer, Lyricist, …).
- `artists: list[ArtistRef] = []`

### Album (core subset)
- `id: int`
- `link: str | None = None`
- `titles: LocalizedText`
- `catalog: str | None = None`
- `release_date: PartialDate | None = None`
- `classification: str | None = None`
- `cover_small: str | None = None`
- `cover_full: str | None = None`
- `discs: list[Disc] = []`
- `credits: list[Credit] = []`
- `notes: str | None = None` — the freeform field the Beta deep-parse later enriches.

## Search models (`search.py`)

### AlbumSearchResult
- `id: int`
- `link: str | None = None`
- `titles: LocalizedText`
- `catalog: str | None = None`
- `release_date: PartialDate | None = None`

### SearchResults
- `query: str`
- `albums: list[AlbumSearchResult] = []`

Scoped to albums only for the MVP. Other vgmdb search categories (artists, products,
organizations) are deferred to B3.

## Conventions

- Every model sets `model_config = ConfigDict(extra="forbid", frozen=True)`:
  - **`extra="forbid"`** — because *we* construct these from our own parser, unexpected keys
    signal a parser bug rather than tolerable noise.
  - **`frozen=True`** — models are immutable value objects; parsers build them via the
    constructor in one shot. Prevents accidental mutation by consumers and gives value
    semantics (hashable, comparable).
- Optional fields default to `None`; list fields default to empty. A parser that produces only
  partial data still yields a valid model.

## Testing strategy

Pure unit tests, no I/O:

- **LocalizedText**: `prefer` (hit / miss-falls-back), `default` (English/Romaji preference,
  empty → `None`), `all`, `__str__`.
- **PartialDate**: field validation (bad month/day rejected, day-without-month rejected),
  `precision`, `__str__` per precision, `parse` round-trips for the three shapes and `None` on
  garbage.
- **Entities** (`Album`, `Disc`, `Track`, `Credit`, `ArtistRef`, search models): construction with
  full and partial data, optional defaults applied, `extra="forbid"` rejects unknown keys,
  `frozen=True` rejects mutation, `model_dump()` / round-trip integrity.

## Acceptance criteria (from the epic)

- `Album` / `Track` / `Credit` and search-result models defined as pydantic v2.
- Importable from the package.
- Typed and documented.

## Open questions / deferrals

- **Parsed track duration** — `Track.length` stays a raw string for MVP; a `timedelta`-based
  field can be added later without breaking consumers.
- **LocalizedText language keys** — we store vgmdb's language labels verbatim (e.g. "English",
  "Japanese", "Romaji"); normalization to ISO codes is out of scope.
