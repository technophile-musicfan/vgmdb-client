# Enrichment

vgmdb album pages often describe per-track credits only in freeform **notes** rather than structured
fields. The optional enrichment layer extracts those into an `AlbumEnrichment` (per-track `Credit`s),
through a pluggable backend. It is opt-in and additive — the base `Album` is fully usable without it.

```python
from vgmdb_client.enrich import enrich_album, RuleBasedBackend

album = client.get_album(4)
enrichment = enrich_album(album, backend=RuleBasedBackend())
for track_number, credits in enrichment.track_credits.items():
    for credit in credits:
        print(track_number, credit.role, [a.names.default for a in credit.artists])
```

With no backend, `enrich_album` returns an empty `AlbumEnrichment` (graceful no-op).

## Backends

- **`RuleBasedBackend`** — deterministic, dependency-free. Conservative regex rules over the notes
  (inline `Name (tracks)` parentheticals and `Role by Names` blocks under a track-range header).
  Favors precision: a credit with no track reference is dropped.
- **`OpenAICompatibleBackend`** — sends the tracklist + notes to an OpenAI-compatible
  `/chat/completions` endpoint, validates the reply, and retries once on a malformed response.
  Customizable prompt and output mode (`json_object` / `json_schema` / `tool`).

```python
from vgmdb_client.enrich import OpenAICompatibleBackend

backend = OpenAICompatibleBackend(url="https://api.example/v1/chat/completions",
                                  model="gpt-4o-mini", api_key="...")
enrichment = enrich_album(album, backend=backend)
```

A configured backend that fails raises `EnrichmentError`. You can also build an LLM backend from
environment variables (`LLM_URL` / `LLM_MODEL` / `LLM_API_KEY` / `LLM_OUTPUT_MODE`) via
`backend_from_env()`, which returns `None` when `LLM_URL` is unset.

Backends implement the small `EnrichmentBackend` protocol, so you can supply your own.
