# Client guide

`Client` (synchronous) and `AsyncClient` (asynchronous) share the same API: construct one with
credentials or a `TransportConfig`, then fetch entities. Both are context managers that close the
underlying transport on exit.

## Constructing a client

The convenient path is from a browser cURL paste (see [authentication](authentication.md)):

```python
from vgmdb_client import Client
from vgmdb_client.auth import Credentials

client = Client.from_credentials(Credentials.from_curl(curl))
```

Or build the transport config directly — useful when you already hold the token and User-Agent:

```python
from vgmdb_client import Client, TransportConfig

config = TransportConfig(user_agent="Mozilla/5.0 ...", cf_clearance="<token>")
client = Client(config=config)
```

`from_credentials` forwards extra `TransportConfig` keyword overrides, e.g. `min_interval=0` to
disable the politeness throttle, or `timeout=20.0`.

## Fetching entities

```python
with Client.from_credentials(creds) as client:
    album = client.get_album(4)              # -> Album
    results = client.search("final fantasy") # -> SearchResults
    artist = client.get_artist(146)          # -> Artist
    product = client.get_product(262)        # -> Product
    org = client.get_organization(17)        # -> Organization
    event = client.get_event(149)            # -> Event
```

See [entities](entities.md) for the model fields.

## Async

`AsyncClient` mirrors `Client` method-for-method; everything is awaitable and it is an async context
manager:

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

Given the same page HTML, `Client` and `AsyncClient` return equal models.

## Errors

The client adds no error semantics — transport and parser errors propagate unchanged:

- `CloudflareChallengeError` — missing/stale token (not retried; refresh and retry, see
  [authentication](authentication.md)).
- `NotFoundError` — a real 404 for the requested resource.
- `RateLimitedError` — a 429, exposing `retry_after` when the server provided it.
- `TransientTransportError` — connection/timeout/5xx, raised only after retries are exhausted.
- `ParseError` (e.g. `NotAnAlbumPageError`) — the fetched HTML was not the expected page.

All inherit from `VgmdbClientError`, so you can catch the whole family at once.
