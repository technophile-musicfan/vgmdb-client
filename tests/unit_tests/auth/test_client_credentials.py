"""Tests for Client/AsyncClient credential fill (from_credentials) and renew (set_credentials)."""

from __future__ import annotations

import asyncio

import pytest

from tests.support.fixtures import load_album_fixture
from vgmdb_client import AsyncClient, Client
from vgmdb_client.auth import Credentials
from vgmdb_client.client._core import album_path
from vgmdb_client.transport.errors import CloudflareChallengeError

_UA = "Mozilla/5.0 Chrome/120"
CREDS = Credentials(cf_clearance="TOK", user_agent=_UA)
FRESH = Credentials(cf_clearance="TOK2", user_agent="UA/2.0")


class RecordingSyncTransport:
    """A duck-typed SyncTransport recording credential updates."""

    def __init__(self) -> None:
        self.cf_clearance: str | None = None
        self.user_agent: str | None = None
        self.closed = False

    def set_cf_clearance(self, token: str) -> None:
        self.cf_clearance = token

    def set_user_agent(self, user_agent: str) -> None:
        self.user_agent = user_agent

    def get(self, path: str) -> str:  # pragma: no cover - not exercised here
        return ""

    def close(self) -> None:
        self.closed = True


class RecordingAsyncTransport(RecordingSyncTransport):
    async def aclose(self) -> None:
        self.closed = True


def test_from_credentials_builds_client_carrying_pair() -> None:
    with Client.from_credentials(CREDS) as client:
        config = client._transport._config  # type: ignore[attr-defined]
        assert config.cf_clearance == "TOK"
        assert config.user_agent == _UA


def test_from_credentials_forwards_overrides() -> None:
    with Client.from_credentials(CREDS, min_interval=0) as client:
        assert client._transport._config.min_interval == 0  # type: ignore[attr-defined]
        assert client._transport._config.cf_clearance == "TOK"  # type: ignore[attr-defined]


def test_set_credentials_swaps_pair() -> None:
    stub = RecordingSyncTransport()
    Client(transport=stub).set_credentials(FRESH)  # type: ignore[arg-type]
    assert stub.cf_clearance == "TOK2"
    assert stub.user_agent == "UA/2.0"


def test_async_from_credentials_builds_client_carrying_pair() -> None:
    client = AsyncClient.from_credentials(CREDS)
    config = client._transport._config  # type: ignore[attr-defined]
    assert config.cf_clearance == "TOK"
    assert config.user_agent == _UA
    asyncio.run(client.aclose())


def test_async_set_credentials_swaps_pair() -> None:
    stub = RecordingAsyncTransport()
    AsyncClient(transport=stub).set_credentials(FRESH)  # type: ignore[arg-type]
    assert stub.cf_clearance == "TOK2"
    assert stub.user_agent == "UA/2.0"


class StaleThenFreshTransport(RecordingSyncTransport):
    """Raises a Cloudflare challenge until the FRESH cf_clearance is applied, then serves HTML."""

    def __init__(self, html_by_path: dict[str, str]) -> None:
        super().__init__()
        self._html = html_by_path

    def get(self, path: str) -> str:
        if self.cf_clearance != "TOK2":
            raise CloudflareChallengeError
        return self._html[path]


def test_renewal_after_cloudflare_challenge() -> None:
    html, golden = load_album_fixture(4)
    client = Client(transport=StaleThenFreshTransport({album_path(4): html}))  # type: ignore[arg-type]
    with pytest.raises(CloudflareChallengeError):
        client.get_album(4)
    client.set_credentials(FRESH)  # re-paste a fresh cURL and swap it in
    assert client.get_album(4) == golden
