## Context

M1 is the pydantic v2 model layer — the typed vocabulary M3 parsers produce, M4 client returns,
and M5 fixtures assert against. It is pure: no I/O, no parsing. `pydantic` is already a runtime
dependency (added by the transport layer). Source of truth: `docs/superpowers/vgmdb_client/2026-06-15_models_design.md`.

Constraints driven by vgmdb's data shape: titles/names are multi-language; release dates are
often partial (year-only or year-month); credit roles are open-ended.

## Goals / Non-Goals

**Goals:**
- Shared value types: `LocalizedText`, `PartialDate`, `ArtistRef`.
- Album entity (core subset): `Album`, `Disc`, `Track`, `Credit`.
- Albums-only search: `AlbumSearchResult`, `SearchResults`.
- Immutable, unknown-key-rejecting models that still accept partial data.

**Non-Goals:**
- HTML→model parsing — M3 (`vgmdb-v9g.6`).
- Track-level/freeform enrichment — B1 (`vgmdb-bzf.1`).
- Full Artist/Product/Organization entities and non-album search categories — B3 (`vgmdb-bzf.3`).
- Album fields beyond the core subset (products, related, stores, reviews, ratings, websites,
  distributor, barcode).

## Decisions

**D1 — `LocalizedText` as a `RootModel[dict[str, str]]` with accessors.**
Centralizes "pick a language" logic (`prefer(*langs)`, `default`, `all`, `__str__`). *Alternative:*
plain `dict[str, str]` — rejected; it scatters language-selection logic across every consumer.
Storing a single canonical string was rejected as data loss.

**D2 — `PartialDate` (year + optional month/day) with a `parse` classmethod.**
vgmdb dates are frequently incomplete; a strict `date` would discard year-only/year-month values.
Validation rejects out-of-range month/day and a day without a month. `parse` lives on the model so
M3 and tests share one implementation. *Alternative:* raw string — rejected; pushes precision
handling onto every consumer. `date | None` — rejected; lossy.

**D3 — Credits as `list[Credit{role, artists: list[ArtistRef]}]`.**
Roles are open-ended on vgmdb; a flexible list beats fixed `composers/arrangers/...` fields that
break on uncommon roles. `ArtistRef` is a lightweight pointer (names + optional id/link), distinct
from the future full `Artist` entity.

**D4 — Core album subset only.**
Ship the fields a first useful album fetch needs (titles, catalog, release date, cover, tracklist,
credits, classification, notes). Richer fields are additive later and don't break frozen models.

**D5 — Albums-only search.**
The MVP is album + search; modeling artist/product/org search categories now is premature. Adding
them later is additive.

**D6 — `frozen=True, extra="forbid"` on every model.**
We construct these from our own parser, so unknown keys signal a parser bug, and immutability gives
value semantics and prevents accidental consumer mutation. Parsers build via the constructor in one
shot. Optional fields default to `None`/empty so partial parser output stays valid.

## Risks / Trade-offs

- **Frozen models complicate incremental construction** → parsers assemble a kwargs dict and
  construct once; no post-construction mutation needed.
- **`extra="forbid"` turns vgmdb adding a field into a parser error** → acceptable and desirable:
  we own both the parser and the models, so a surprise key should surface loudly in tests.
- **`Track.length` as a raw string** is less convenient than a duration → kept simple for MVP; a
  parsed-duration field can be added later without breaking consumers.
- **LocalizedText keys are vgmdb's verbatim labels** ("English"/"Japanese"/"Romaji") → no ISO
  normalization; `prefer`/`default` handle the common cases.

## Open Questions

- Whether to later add a parsed `timedelta` track duration alongside the raw `length` — deferred,
  additive.
