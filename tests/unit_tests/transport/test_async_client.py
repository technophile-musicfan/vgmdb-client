"""Tests for AsyncTransport.

Async coroutines are driven via ``asyncio.run`` so no async pytest plugin is
required; respx still intercepts httpx.AsyncClient traffic.
"""

import asyncio
from collections.abc import Awaitable
from typing import TypeVar

import httpx
import pytest
import respx

from vgmdb_client.transport import async_client as async_client_module
from vgmdb_client.transport.async_client import AsyncTransport
from vgmdb_client.transport.config import TransportConfig
from vgmdb_client.transport.errors import (
    CloudflareChallengeError,
    NotFoundError,
    RateLimitedError,
    TransientTransportError,
)
from vgmdb_client.transport.sync_client import SyncTransport

BASE = "https://vgmdb.net"
URL = f"{BASE}/album/123"

T = TypeVar("T")


def _run(coro: Awaitable[T]) -> T:
    return asyncio.run(coro)  # type: ignore[arg-type]


def _config(**kwargs: object) -> TransportConfig:
    defaults: dict[str, object] = {
        "user_agent": "UA/1.0",
        "cf_clearance": "token",
        "min_interval": 0.0,
        "backoff_base": 0.001,
        "backoff_max": 0.01,
    }
    defaults.update(kwargs)
    return TransportConfig(**defaults)  # type: ignore[arg-type]


@respx.mock
def test_async_get_returns_html() -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, text="<html>ok</html>"))

    async def scenario() -> str:
        async with AsyncTransport(_config()) as transport:
            return await transport.get("album/123")

    assert _run(scenario()) == "<html>ok</html>"


@respx.mock
def test_async_request_includes_cf_cookie_and_user_agent() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, text="ok"))

    async def scenario() -> None:
        async with AsyncTransport(_config()) as transport:
            await transport.get("album/123")

    _run(scenario())
    request = route.calls.last.request
    assert request.headers["user-agent"] == "UA/1.0"
    assert "cf_clearance=token" in request.headers["cookie"]


@respx.mock
def test_async_404_raises_not_found_not_retried() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(404))

    async def scenario() -> None:
        async with AsyncTransport(_config(max_retries=3)) as transport:
            await transport.get("album/123")

    with pytest.raises(NotFoundError):
        _run(scenario())
    assert route.call_count == 1


@respx.mock
def test_async_cloudflare_challenge_not_retried() -> None:
    route = respx.get(URL).mock(
        return_value=httpx.Response(403, headers={"cf-mitigated": "challenge"})
    )

    async def scenario() -> None:
        async with AsyncTransport(_config(max_retries=3)) as transport:
            await transport.get("album/123")

    with pytest.raises(CloudflareChallengeError):
        _run(scenario())
    assert route.call_count == 1


@respx.mock
def test_async_429_rate_limited_not_retried() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(429, headers={"retry-after": "30"}))

    async def scenario() -> None:
        async with AsyncTransport(_config(max_retries=3)) as transport:
            await transport.get("album/123")

    with pytest.raises(RateLimitedError) as exc:
        _run(scenario())
    assert exc.value.retry_after == 30.0
    assert route.call_count == 1


@respx.mock
def test_async_transient_500_retried_then_succeeds() -> None:
    route = respx.get(URL).mock(side_effect=[httpx.Response(500), httpx.Response(200, text="ok")])

    async def scenario() -> str:
        async with AsyncTransport(_config(max_retries=3)) as transport:
            return await transport.get("album/123")

    assert _run(scenario()) == "ok"
    assert route.call_count == 2


@respx.mock
def test_async_timeout_retried_then_succeeds() -> None:
    route = respx.get(URL).mock(
        side_effect=[httpx.TimeoutException("timed out"), httpx.Response(200, text="ok")]
    )

    async def scenario() -> str:
        async with AsyncTransport(_config(max_retries=3)) as transport:
            return await transport.get("album/123")

    assert _run(scenario()) == "ok"
    assert route.call_count == 2


@respx.mock
def test_async_retries_exhausted_raises_transient() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(500))

    async def scenario() -> None:
        async with AsyncTransport(_config(max_retries=2)) as transport:
            await transport.get("album/123")

    with pytest.raises(TransientTransportError):
        _run(scenario())
    assert route.call_count == 3


@respx.mock
def test_async_set_cf_clearance_updates_cookie() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, text="ok"))

    async def scenario() -> None:
        async with AsyncTransport(_config()) as transport:
            await transport.get("album/123")
            transport.set_cf_clearance("newtoken")
            await transport.get("album/123")

    _run(scenario())
    assert "cf_clearance=newtoken" in route.calls.last.request.headers["cookie"]


@respx.mock
def test_async_set_user_agent_updates_header() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, text="ok"))

    async def scenario() -> None:
        async with AsyncTransport(_config()) as transport:
            await transport.get("album/123")
            transport.set_user_agent("UA/2.0")
            await transport.get("album/123")

    _run(scenario())
    assert route.calls.last.request.headers["user-agent"] == "UA/2.0"


@respx.mock
def test_async_min_interval_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr(async_client_module.asyncio, "sleep", fake_sleep)
    respx.get(URL).mock(return_value=httpx.Response(200, text="ok"))

    async def scenario() -> None:
        async with AsyncTransport(_config(min_interval=5.0)) as transport:
            await transport.get("album/123")
            await transport.get("album/123")

    _run(scenario())
    assert len(sleeps) == 1
    assert 4.0 < sleeps[0] <= 5.0


@respx.mock
def test_async_context_manager_closes_client() -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, text="ok"))
    transport = AsyncTransport(_config())

    async def scenario() -> None:
        async with transport:
            await transport.get("album/123")

    _run(scenario())
    assert transport.is_closed


@respx.mock
def test_async_redirects_are_followed() -> None:
    respx.get(URL).mock(
        return_value=httpx.Response(302, headers={"location": f"{BASE}/album/123/"})
    )
    respx.get(f"{URL}/").mock(return_value=httpx.Response(200, text="<html>final</html>"))

    async def scenario() -> str:
        async with AsyncTransport(_config()) as transport:
            return await transport.get("album/123")

    assert _run(scenario()) == "<html>final</html>"


@respx.mock
def test_sync_and_async_parity_success() -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, text="<html>"))
    with SyncTransport(_config()) as sync_transport:
        sync_result = sync_transport.get("album/123")

    async def scenario() -> str:
        async with AsyncTransport(_config()) as transport:
            return await transport.get("album/123")

    assert sync_result == _run(scenario()) == "<html>"


@respx.mock
def test_sync_and_async_parity_error() -> None:
    respx.get(URL).mock(return_value=httpx.Response(404))
    with SyncTransport(_config()) as sync_transport, pytest.raises(NotFoundError):
        sync_transport.get("album/123")

    async def scenario() -> None:
        async with AsyncTransport(_config()) as transport:
            await transport.get("album/123")

    with pytest.raises(NotFoundError):
        _run(scenario())
