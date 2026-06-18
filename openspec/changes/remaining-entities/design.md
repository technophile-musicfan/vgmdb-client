## Context

vgmdb.net exposes `/album/`, `/artist/`, `/org/`, `/product/`, `/event/`, `/search`; only `/event/`
is unimplemented. There is no `/release/` URL — the concrete "release" datum on an album page is the
`link_event` anchor by the release date. Full brainstorm:
`docs/superpowers/vgmdb_client/2026-06-18_remaining_entities_design.md`.

## Goals / Non-Goals

**Goals:**
- Add the `Event` entity (model + clean-room parser + sync/async client) mirroring the shipped entity pattern.
- Link an album to its release event via an additive `release_event: EventRef | None`.

**Non-Goals:**
- A `/release/` entity (does not exist), a structured editions/printings/reprints list (not in page data),
  released-album/related lists on the Event page, and events in search results.

## Decisions

- **Mirror the established entity pattern (vs. a richer Event or a new capability).** Every entity is a
  frozen `VgmdbModel` + a canonical-link-keyed clean-room parser + `get_*` methods + a fixture/golden.
  `Event` follows it; the change extends the existing `models`/`parsers`/`client` capabilities rather
  than introducing a new one (same as the B3 entities).
- **`release_event` is additive and best-effort.** Default `None`; a missing/malformed `link_event`
  yields `None` and never raises, so existing album goldens stay valid (only fixture 33000 gains a value).
- **Event dates as `start_date`/`end_date` pair.** `end_date` is `None` for single-day events or when
  the page shows no distinct end; the exact field set is confirmed against the captured fixture.

## Risks / Trade-offs

- **No event fixture exists yet.** → The plan sequences capturing a real `/event/` page + golden (and
  confirming album 33000's `link_event`) BEFORE the parser/client tests; the author cannot fetch live.
- **Event page structure is unverified until captured.** → Keep the model a conservative core subset;
  fields without page data stay defaulted rather than invented. Selectors are validated against the
  captured golden, like every other parser.
- **Touching the shipped album parser risks regressing albums.** → The release-event read is isolated
  to the release-date cell and additive; the full existing album test suite must stay green.
