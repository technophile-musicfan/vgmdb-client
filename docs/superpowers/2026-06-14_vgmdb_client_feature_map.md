# vgmdb-client — Feature Map

**Date:** 2026-06-14
**Status:** Vision (Workflow 1)
**Major scope:** `vgmdb_client`
**Companion:** `2026-06-14_vgmdb_client.md`

Feature areas grouped into tiers (MVP / Beta / V1) with a dependency map. Each feature area
becomes a Beads epic.

---

## MVP — "first usable version"

A consumer can fetch an album by ID and run a search, sync or async, against live `vgmdb.net`
with a manually supplied `cf_clearance` token, getting typed pydantic models back.

| ID | Feature area | What it delivers |
|----|--------------|------------------|
| **M1** | **Models (core)** | `pydantic` v2 models: `Album`, `Track`, `Credit`, search-result types. The shared vocabulary every other layer speaks. |
| **M2** | **Transport** | `httpx` sync + async fetcher. Manual `cf_clearance` + `User-Agent` injection. Retries. Typed errors distinguishing a Cloudflare challenge from a real 404. |
| **M3** | **Parsers (album + search)** | Clean-room pure functions `html -> model` for the album page and search results. We own every selector. |
| **M4** | **Client API** | `Client` / `AsyncClient` composing Transport + Parsers over a shared core. Methods: `get_album(id)`, `search(query)`. |
| **M5** | **Fixtures (seed)** | Captured album/search HTML pages + golden expected outputs, wired into the test suite. Foundation for the Beta harness. |

**MVP definition of done:** `get_album` and `search` work against live vgmdb (token supplied),
return validated models, and are covered by fixture-based tests for both sync and async.

---

## Beta — "measure & enrich"

| ID | Feature area | What it delivers |
|----|--------------|------------------|
| **B1** | **Deep-parse helper (LLM/ML)** | Pluggable enrichment of freeform fields (track-level contributions, detailed roles from the Notes/Information tab). First backend: optional `LLM_URL` → OpenAI-compatible HTTP endpoint. Embedded lightweight ML later. Shipped as an opt-in extra. |
| **B2** | **Parsing-quality harness** | Compare **hufman vs. ours vs. ours+LLM** over the fixtures dataset, with quality reporting to rank parser/LLM choices. hufman (MIT) vendored as a **dev-only** benchmark dependency. |
| **B3** | **More entities** | `Artist`, `Product`, `Organization` — models + clean-room parsers + client methods. |

---

## V1 — "complete & polished"

| ID | Feature area | What it delivers |
|----|--------------|------------------|
| **V1a** | **Auth-token helper** | Assist fill/renew of `cf_clearance` (UX/design TBD). Not "beating" Cloudflare. |
| **V1b** | **Remaining entities** | Events, releases, and any remaining vgmdb entity types. |
| **V1c** | **Release polish** | Full docs site (MkDocs), examples, PyPI publish. |

---

## Dependency map

```
M1 Models ─┬──> M3 Parsers ───> M4 Client ──(needs)──> M2 Transport
           │
           └──> M5 Fixtures ──> M3 Parsers (test target)

M1, M3 ─────────> B1 Deep-parse (LLM/ML)

M3, M5 ─┐
B1 ─────┼───────> B2 Parsing-quality harness
hufman ─┘         (MIT, dev-only benchmark adapter)

M1, M3, M4 ─────> B3 More entities (Artist / Product / Org)

M2 ─────────────> V1a Auth-token helper

M1, M3, M4 ─────> V1b Remaining entities (Events, releases)

(all) ──────────> V1c Release polish
```

**Reading the graph:**
- **M1 Models** and **M2 Transport** are the two independent foundations; everything else
  builds on them.
- **M3 Parsers** need Models, and are validated by **M5 Fixtures**.
- **M4 Client** is the integration point (Transport + Parsers).
- **B1 Deep-parse** and **B2 Harness** both build on a working parser; the harness additionally
  consumes the hufman baseline and B1's enriched output.
- **V1a Auth helper** depends only on Transport and is otherwise independent.

## Build order (suggested)

1. M1 → M2 (parallelizable) → M3 → M5 → M4  ⟶ **MVP**
2. B3 (more entities) and B1 (deep-parse) in parallel → B2 (harness)  ⟶ **Beta**
3. V1a → V1b → V1c  ⟶ **V1**
