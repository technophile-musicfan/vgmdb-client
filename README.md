# vgmdb-client

[![Release](https://img.shields.io/github/v/release/HOZHENWAI/vgmdb-client)](https://github.com/HOZHENWAI/vgmdb-client/releases)
[![Build status](https://img.shields.io/github/actions/workflow/status/HOZHENWAI/vgmdb-client/main.yml?branch=main)](https://github.com/HOZHENWAI/vgmdb-client/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/HOZHENWAI/vgmdb-client/branch/main/graph/badge.svg)](https://codecov.io/gh/HOZHENWAI/vgmdb-client)
[![License](https://img.shields.io/github/license/HOZHENWAI/vgmdb-client)](https://github.com/HOZHENWAI/vgmdb-client/blob/main/LICENSE)

A typed, sync + async Python client for [vgmdb.net](https://vgmdb.net) — the community database of
video-game and anime music. It fetches and parses albums, artists, products, organizations, and
events into validated [pydantic](https://docs.pydantic.dev) models, with its own clean-room HTML
parsers.

- **Documentation:** <https://HOZHENWAI.github.io/vgmdb-client/>
- **Source:** <https://github.com/HOZHENWAI/vgmdb-client/>

## Features

- **Sync and async** — `Client` and `AsyncClient` share the same typed API.
- **Typed models** — `Album`, `Track`, `Credit`, `Artist`, `Product`, `Organization`, `Event`,
  search results — immutable pydantic v2 models.
- **Cloudflare-aware transport** — manual `cf_clearance` + `User-Agent` injection, typed errors that
  distinguish a Cloudflare challenge from a real 404, retries, and a politeness throttle.
- **Auth helper** — paste a browser "Copy as cURL" and `Credentials.from_curl` extracts the
  `cf_clearance` + matching `User-Agent` pair for you. (It assists with the token; it does **not**
  defeat the Cloudflare challenge — you solve that in your own browser.)
- **Optional enrichment** — pluggable backends (deterministic rule-based, or an OpenAI-compatible
  LLM endpoint) to extract per-track credits from freeform album notes.
- **No heavy dependencies** — just `httpx`, `pydantic`, `lxml`, and `tenacity`.

## Installation

```bash
pip install vgmdb-client
```

## Quickstart

vgmdb.net is behind Cloudflare, so a request needs a valid `cf_clearance` cookie paired with the
exact `User-Agent` it was issued for. Solve the challenge once in your browser, open devtools, copy
any request to vgmdb.net as **cURL (bash)**, and hand it to the client:

```python
from vgmdb_client import Client
from vgmdb_client.auth import Credentials

curl = """curl 'https://vgmdb.net/album/4' \\
  -H 'user-agent: Mozilla/5.0 ...' \\
  -H 'cookie: cf_clearance=<your-token>; ...'"""

with Client.from_credentials(Credentials.from_curl(curl)) as client:
    album = client.get_album(4)
    print(album.titles.default, album.release_date)

    results = client.search("final fantasy")
    for hit in results.albums[:5]:
        print(hit.catalog, hit.titles.default)
```

The async client mirrors it:

```python
import asyncio
from vgmdb_client import AsyncClient
from vgmdb_client.auth import Credentials

async def main() -> None:
    async with AsyncClient.from_credentials(Credentials.from_curl(curl)) as client:
        album = await client.get_album(4)
        print(album.titles.default)

asyncio.run(main())
```

When a token goes stale you'll get a `CloudflareChallengeError`; grab a fresh cURL and re-apply it
without rebuilding the client:

```python
from vgmdb_client.transport.errors import CloudflareChallengeError

try:
    album = client.get_album(4)
except CloudflareChallengeError:
    client.set_credentials(Credentials.from_curl(fresh_curl))
    album = client.get_album(4)
```

See the [documentation](https://HOZHENWAI.github.io/vgmdb-client/) for the full API, authentication,
entities, and enrichment guides.

## Attribution & use

Data comes from [vgmdb.net](https://vgmdb.net) and its contributors. This is an unofficial client;
please use it responsibly — keep the politeness throttle enabled and respect vgmdb.net's terms.

## License

MIT — see [LICENSE](LICENSE).
