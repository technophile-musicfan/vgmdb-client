"""Auth helper: turn a browser cURL paste into client credentials.

Assists filling and renewing the ``cf_clearance`` token + matching ``User-Agent``; it does NOT
defeat, solve, or automate the Cloudflare challenge — the human passes it in their own browser,
copies the request as cURL (bash), and pastes it here.

Fill (initial setup) and renew (after a stale token) follow the same paste-a-cURL path::

    from vgmdb_client import Client
    from vgmdb_client.auth import Credentials
    from vgmdb_client.transport.errors import CloudflareChallengeError

    client = Client.from_credentials(Credentials.from_curl(curl_text))
    try:
        album = client.get_album(4)
    except CloudflareChallengeError:
        # token went stale — re-solve in the browser, copy a fresh cURL, re-apply, retry
        client.set_credentials(Credentials.from_curl(fresh_curl))
        album = client.get_album(4)
"""

from __future__ import annotations

from vgmdb_client.auth.credentials import Credentials
from vgmdb_client.auth.errors import CurlParseError

__all__ = ["Credentials", "CurlParseError"]
