# vgmdb-client

A typed, sync + async Python client for [vgmdb.net](https://vgmdb.net) — the community database of
video-game and anime music. It fetches and parses albums, artists, products, organizations, and
events into validated [pydantic](https://docs.pydantic.dev) v2 models, using its own clean-room HTML
parsers.

## Installation

```bash
pip install vgmdb-client
```

The base install is dependency-light (`httpx`, `pydantic`, `lxml`, `tenacity`).

## Quickstart

vgmdb.net is behind Cloudflare: a request only succeeds with a valid `cf_clearance` cookie paired
with the exact `User-Agent` it was issued for. Solve the challenge once in your browser, open
devtools, copy any request to vgmdb.net as **cURL (bash)**, and hand it to the client — the
[authentication guide](guides/authentication.md) explains the flow.

```python
from vgmdb_client import Client
from vgmdb_client.auth import Credentials

curl = """curl 'https://vgmdb.net/album/4' \\
  -H 'user-agent: Mozilla/5.0 ...' \\
  -H 'cookie: cf_clearance=<your-token>; ...'"""

with Client.from_credentials(Credentials.from_curl(curl)) as client:
    album = client.get_album(4)
    print(album.titles.default, album.release_date)
```

## Where to next

- [Client guide](guides/client.md) — fetching albums, search, and the other entities, sync and async.
- [Authentication](guides/authentication.md) — the `cf_clearance` flow, `Credentials`, and renewal.
- [Entities](guides/entities.md) — the data models you get back.
- [Enrichment](guides/enrichment.md) — optional per-track credit extraction from freeform notes.
- [API reference](reference/client.md) — the full generated API.

## Scope & attribution

This is an **unofficial** client. Data is © [vgmdb.net](https://vgmdb.net) and its contributors; use
it responsibly, keep the politeness throttle enabled, and respect the site's terms. The auth helper
assists you in supplying a token you obtained in your own browser — it does **not** defeat or
automate the Cloudflare challenge.
