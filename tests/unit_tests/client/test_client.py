"""Tests for the sync Client and async AsyncClient (offline, via stub transports)."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

import pytest

from tests.support.fixtures import load_album_fixture, load_search_fixture
from vgmdb_client import AsyncClient, Client, NotFoundError, ParseError, TransportConfig
from vgmdb_client.client._core import album_path, search_path

T = TypeVar("T")


def _run(coro: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coro)


class StubSyncTransport:
    """A duck-typed SyncTransport returning canned HTML by path."""

    def __init__(self, html_by_path: dict[str, str] | None = None, *, error: Exception | None = None) -> None:
        self._html = html_by_path or {}
        self._error = error
        self.closed = False

    def get(self, path: str) -> str:
        if self._error is not None:
            raise self._error
        return self._html[path]

    def close(self) -> None:
        self.closed = True


class StubAsyncTransport:
    """A duck-typed AsyncTransport returning canned HTML by path."""

    def __init__(self, html_by_path: dict[str, str] | None = None, *, error: Exception | None = None) -> None:
        self._html = html_by_path or {}
        self._error = error
        self.closed = False

    async def get(self, path: str) -> str:
        if self._error is not None:
            raise self._error
        return self._html[path]

    async def aclose(self) -> None:
        self.closed = True


# --- sync client --------------------------------------------------------------------------


@pytest.mark.parametrize("album_id", [271, 4])
def test_get_album_returns_golden(album_id: int) -> None:
    html, golden = load_album_fixture(album_id)
    client = Client(transport=StubSyncTransport({album_path(album_id): html}))
    assert client.get_album(album_id) == golden


def test_search_near_empty_returns_golden() -> None:
    html, golden = load_search_fixture("near-empty")
    client = Client(transport=StubSyncTransport({search_path(golden.query): html}))
    assert client.search(golden.query) == golden


def test_search_multi_hit_first_10() -> None:
    html, golden = load_search_fixture("multi-hit")
    client = Client(transport=StubSyncTransport({search_path(golden.query): html}))
    result = client.search(golden.query)
    assert result.query == golden.query
    assert result.albums[:10] == golden.albums


def test_context_manager_closes_transport() -> None:
    stub = StubSyncTransport()
    with Client(transport=stub):
        pass
    assert stub.closed is True


def test_transport_error_propagates() -> None:
    client = Client(transport=StubSyncTransport(error=NotFoundError()))
    with pytest.raises(NotFoundError):
        client.get_album(1)


def test_parse_error_propagates() -> None:
    client = Client(transport=StubSyncTransport({album_path(1): "<html><body><h1>nope</h1></body></html>"}))
    with pytest.raises(ParseError):
        client.get_album(1)


def test_construction_requires_exactly_one_source() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        Client()
    with pytest.raises(ValueError, match="exactly one"):
        Client(config=TransportConfig(user_agent="x"), transport=StubSyncTransport())


# --- async client -------------------------------------------------------------------------


def test_async_get_album_returns_golden() -> None:
    html, golden = load_album_fixture(271)
    client = AsyncClient(transport=StubAsyncTransport({album_path(271): html}))
    assert _run(client.get_album(271)) == golden


def test_async_search_returns_golden() -> None:
    html, golden = load_search_fixture("near-empty")
    client = AsyncClient(transport=StubAsyncTransport({search_path(golden.query): html}))
    assert _run(client.search(golden.query)) == golden


def test_async_context_manager_closes_transport() -> None:
    stub = StubAsyncTransport()

    async def use() -> None:
        async with AsyncClient(transport=stub):
            pass

    _run(use())
    assert stub.closed is True


def test_sync_and_async_agree() -> None:
    html, _ = load_album_fixture(5012)
    sync_result = Client(transport=StubSyncTransport({album_path(5012): html})).get_album(5012)
    async_result = _run(AsyncClient(transport=StubAsyncTransport({album_path(5012): html})).get_album(5012))
    assert sync_result == async_result


# --- public API ---------------------------------------------------------------------------


def test_public_api_surface() -> None:
    import vgmdb_client

    expected = {
        "Client",
        "AsyncClient",
        "Album",
        "SearchResults",
        "TransportConfig",
        "NotFoundError",
        "ParseError",
        "VgmdbClientError",
    }
    assert expected <= set(vgmdb_client.__all__)
    for name in expected:
        assert getattr(vgmdb_client, name) is not None
