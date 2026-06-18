# Authentication

vgmdb.net is behind Cloudflare. A request only succeeds when it carries a valid `cf_clearance`
cookie **paired with the exact `User-Agent`** the token was issued for (the token is bound to that
User-Agent and your IP). A mismatched pair is rejected.

!!! note "Assist, not defeat"
    This helper does **not** solve, defeat, or automate the Cloudflare challenge. You pass the
    challenge yourself in a normal browser; the helper only transports the resulting credentials
    into the client.

## Getting the credentials

1. Visit vgmdb.net in your browser and pass any Cloudflare check so the page loads.
2. Open devtools → Network, reload, right-click a request to `vgmdb.net`, and **Copy → Copy as cURL
   (bash)**.
3. Hand that cURL string to `Credentials.from_curl` — it extracts both the `cf_clearance` cookie and
   the matching `User-Agent` from the one paste, keeping them together as a unit:

```python
from vgmdb_client.auth import Credentials

creds = Credentials.from_curl(curl_text)
# creds.cf_clearance, creds.user_agent
```

If the paste lacks a `cf_clearance` cookie or a `User-Agent`, you get a `CurlParseError`.

## Using the credentials

Build a client directly:

```python
from vgmdb_client import Client

client = Client.from_credentials(creds)
```

Or turn the pair into a `TransportConfig` (forwarding any extra config):

```python
config = creds.to_config(min_interval=0)  # e.g. disable the throttle
```

## Renewing a stale token

`cf_clearance` tokens expire. When one does, the next request raises `CloudflareChallengeError` (it
is deliberately **not** retried — retrying a dead token won't help). Re-solve in your browser, copy a
fresh cURL, and swap the pair into the live client with `set_credentials` — no need to rebuild it:

```python
from vgmdb_client.transport.errors import CloudflareChallengeError

try:
    album = client.get_album(4)
except CloudflareChallengeError:
    client.set_credentials(Credentials.from_curl(fresh_curl))
    album = client.get_album(4)
```

## Supported cURL format

The parser targets the **bash** "Copy as cURL" form (single-quoted, `-H 'Header: value'`) emitted by
Chrome and Firefox. Hand-edited or non-bash forms (Windows `cmd` `^`-continuations, PowerShell,
glued short flags like `-AUA`) are not parsed yet — copy the bash form.
