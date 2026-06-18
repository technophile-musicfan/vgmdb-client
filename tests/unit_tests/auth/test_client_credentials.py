"""Tests for Client/AsyncClient credential fill (from_credentials) and renew (set_credentials)."""

from __future__ import annotations

import asyncio

from vgmdb_client import AsyncClient, Client
from vgmdb_client.auth import Credentials

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
