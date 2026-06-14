# vgmdb-client — Product Vision

**Date:** 2026-06-14
**Status:** Vision (Workflow 1)
**Major scope:** `vgmdb_client`

## Problem

[vgmdb.net](https://vgmdb.net) — the Video Game Music Database — exposes **no official API**.
There is no supported way to query its data programmatically.

The community filled this gap with [hufman/vgmdb](https://github.com/hufman/vgmdb) (the
project behind `vgmdb.info`), but it is **a website, not a client library**: its parsing
logic is tightly coupled to its own web service, and it ships no reusable client. To use it
reliably you must either:

1. depend on a third-party hosted instance (`vgmdb.info`) — raising confidentiality,
   availability, and network-reliability concerns; or
2. self-host the service via Docker and talk to it over HTTP — operational overhead the
   author of this project does not want.

There is no way to *just import a Python package and reliably read vgmdb data*.

## Vision

**A reusable, typed Python client library that talks directly to `vgmdb.net`, parses its
HTML into structured models, and depends on no third-party service.**

"Done" for the first version means a consumer can:

```python
from vgmdb_client import Client

client = Client(cf_clearance="<token>", user_agent="<matching-UA>")
album = client.get_album(123)          # -> typed pydantic Album
results = client.search("nier")        # -> typed search results
```

…with an `AsyncClient` offering the same surface, and the whole thing installable from PyPI
with no Docker and no external dependency on `vgmdb.info`.

## Principles

- **No third-party runtime dependency.** We fetch and parse `vgmdb.net` ourselves. The only
  network endpoint the runtime library touches is vgmdb itself (plus an *optional*,
  user-configured LLM endpoint).
- **Clean-room parsing.** We derive every selector ourselves and own the parsing rules. We do
  **not** trust or reuse hufman's parser in the runtime path. (hufman is used only as a
  dev-time benchmark baseline — see the harness, Beta.)
- **Typed, validated public surface.** Data is returned as `pydantic` v2 models.
- **Both sync and async**, over a single shared parsing/model core (no duplicated logic).
- **Light core, opt-in extras.** LLM/ML enrichment, the benchmark harness, and the auth helper
  are separable extras so the base install stays small.
- **Parsing quality is measurable, not assumed.** A fixtures dataset + comparison harness let
  us empirically judge our parser and any LLM-assisted enrichment.

## Architecture

A layered library:

```
        ┌─────────────────────────────────────────────┐
        │  Public API:  Client (sync)  /  AsyncClient   │
        │     get_album(id) · search(query) · …         │
        └───────────────┬───────────────────────────────┘
                        │ shared core
   ┌────────────────────┼────────────────────┐
   │                    │                     │
┌──▼─────────┐   ┌──────▼────────┐    ┌───────▼────────┐
│ Transport  │   │   Parsers     │    │    Models       │
│ (httpx)    │   │ (clean-room   │    │ (pydantic v2)   │
│ sync+async │   │  HTML→models) │    │ Album, Track,   │
│ CF cookie  │   │ album, search │    │ Credit, Search… │
│ retry/errs │   └──────┬────────┘    └────────▲────────┘
└────────────┘          │                      │
                        └──────────────────────┘
        ┌───────────────────────────────────────────────┐
        │  Opt-in utilities (separable, pluggable)       │
        │  • Deep-parse helper (LLM/ML) for freeform     │
        │    fields → track-level credits, detailed roles│
        │  • Auth-token helper (fill/renew cf_clearance) │
        │  • Fixtures dataset + parsing-quality harness   │
        │    (hufman vs ours vs ours+LLM)                │
        └───────────────────────────────────────────────┘
```

### Layers

- **Transport** — `httpx`-based, sync + async. Owns the Cloudflare reality: the caller injects
  a `cf_clearance` cookie + a matching `User-Agent`. Provides retries and **typed errors** that
  distinguish a Cloudflare challenge from a genuine 404 / not-found. The runtime library does
  **not** attempt to beat Cloudflare.
- **Models** — `pydantic` v2 models: `Album`, `Track`, `Credit`, search-result types, growing
  to `Artist`, `Product`, `Organization`, etc. in later tiers.
- **Parsers** — **pure functions**, `html: str -> Model`. Being pure and side-effect free is
  what makes them independently testable against fixtures and pluggable into the comparison
  harness.
- **Public API** — `Client` / `AsyncClient` compose Transport + Parsers + Models. The shared
  core means async and sync never duplicate parsing logic.

### Opt-in utilities

- **Deep-parse helper (LLM/ML).** Some albums encode richer information than the structured
  page exposes — e.g. *track-level* contributions instead of album-level, or more specific
  roles buried in the freeform "Notes / Information" tab. This helper enriches those freeform
  fields. Pluggable backends:
  - **HTTP LLM** (first): an optional `LLM_URL`-style env var pointing at an **OpenAI-compatible
    endpoint** (typically a self-hosted lightweight model).
  - **Embedded ML** (later): must be lightweight; exact model TBD.
- **Auth-token helper.** Assists the user in filling/renewing `cf_clearance`. Explicitly *not*
  about defeating Cloudflare login. Design finalized later (V1).
- **Fixtures + parsing-quality harness.** A captured dataset of vgmdb HTML pages with golden
  expected outputs, plus a harness that compares **hufman vs. our parser vs. our parser + LLM
  deep-parse** so parsing quality (and the value of a given LLM) can be judged empirically.
  hufman is **MIT-licensed**, so it may be vendored as a **dev-only benchmark dependency**; it
  never enters the runtime library.

## Scope of the first usable version (MVP)

Entities/operations:
- **Albums by ID** — the central, richest entity (tracklist, credits, covers, release info,
  notes).
- **Search** — free-text query returning result lists with IDs to then fetch.

Everything else — Artists, Products, Organizations, Events, the LLM deep-parse, the harness,
and the auth helper — is explicitly **later-tier** (see the feature map).

## Non-goals (for now)

- Defeating or automating Cloudflare login/challenge.
- Write operations against vgmdb (edits, collection management).
- Depending on or wrapping the `vgmdb.info` service at runtime.

## Open questions (resolve when reached, not now)

1. **Deep-parse backend contract** — the exact interface separating "HTTP LLM endpoint" from
   "embedded lightweight ML model". First cut: optional `LLM_URL` → OpenAI-compatible endpoint.
2. **Embedded ML model choice** — must be lightweight; deferred.
3. **Auth-token helper UX** — how the user fills/renews `cf_clearance` (V1).

## Related documents

- Feature map & dependency graph: `2026-06-14_vgmdb_client_feature_map.md`
