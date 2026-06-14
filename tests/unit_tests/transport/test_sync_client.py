"""Tests for SyncTransport."""

import httpx
import pytest
import respx

from vgmdb_client.transport import sync_client as sync_client_module
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
def test_get_returns_html() -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, text="<html>ok</html>"))
    with SyncTransport(_config()) as transport:
        assert transport.get("album/123") == "<html>ok</html>"


@respx.mock
def test_request_includes_cf_cookie_and_user_agent() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, text="ok"))
    with SyncTransport(_config()) as transport:
        transport.get("album/123")
    request = route.calls.last.request
    assert request.headers["user-agent"] == "UA/1.0"
    assert "cf_clearance=token" in request.headers["cookie"]


@respx.mock
def test_404_raises_not_found_and_is_not_retried() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(404))
    with SyncTransport(_config(max_retries=3)) as transport, pytest.raises(NotFoundError):
        transport.get("album/123")
    assert route.call_count == 1


@respx.mock
def test_cloudflare_challenge_raises_and_is_not_retried() -> None:
    route = respx.get(URL).mock(
        return_value=httpx.Response(403, headers={"cf-mitigated": "challenge"})
    )
    with SyncTransport(_config(max_retries=3)) as transport, pytest.raises(CloudflareChallengeError):
        transport.get("album/123")
    assert route.call_count == 1


@respx.mock
def test_429_raises_rate_limited_not_retried() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(429, headers={"retry-after": "30"}))
    with SyncTransport(_config(max_retries=3)) as transport, pytest.raises(RateLimitedError) as exc:
        transport.get("album/123")
    assert exc.value.retry_after == 30.0
    assert route.call_count == 1


@respx.mock
def test_transient_500_retried_then_succeeds() -> None:
    route = respx.get(URL).mock(
        side_effect=[httpx.Response(500), httpx.Response(200, text="ok")]
    )
    with SyncTransport(_config(max_retries=3)) as transport:
        assert transport.get("album/123") == "ok"
    assert route.call_count == 2


@respx.mock
def test_timeout_is_retried_then_succeeds() -> None:
    route = respx.get(URL).mock(
        side_effect=[httpx.TimeoutException("timed out"), httpx.Response(200, text="ok")]
    )
    with SyncTransport(_config(max_retries=3)) as transport:
        assert transport.get("album/123") == "ok"
    assert route.call_count == 2


@respx.mock
def test_retries_exhausted_raises_transient() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(500))
    with SyncTransport(_config(max_retries=2)) as transport, pytest.raises(TransientTransportError):
        transport.get("album/123")
    assert route.call_count == 3  # max_retries + 1


@respx.mock
def test_set_cf_clearance_updates_cookie() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, text="ok"))
    with SyncTransport(_config()) as transport:
        transport.get("album/123")
        transport.set_cf_clearance("newtoken")
        transport.get("album/123")
    assert "cf_clearance=newtoken" in route.calls.last.request.headers["cookie"]


@respx.mock
def test_set_user_agent_updates_header() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, text="ok"))
    with SyncTransport(_config()) as transport:
        transport.get("album/123")
        transport.set_user_agent("UA/2.0")
        transport.get("album/123")
    assert route.calls.last.request.headers["user-agent"] == "UA/2.0"


@respx.mock
def test_min_interval_enforced_between_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(sync_client_module.time, "sleep", lambda seconds: sleeps.append(seconds))
    respx.get(URL).mock(return_value=httpx.Response(200, text="ok"))
    with SyncTransport(_config(min_interval=5.0)) as transport:
        transport.get("album/123")
        transport.get("album/123")
    assert len(sleeps) == 1
    assert 4.0 < sleeps[0] <= 5.0


@respx.mock
def test_redirects_are_followed() -> None:
    respx.get(URL).mock(
        return_value=httpx.Response(302, headers={"location": f"{BASE}/album/123/"})
    )
    respx.get(f"{URL}/").mock(return_value=httpx.Response(200, text="<html>final</html>"))
    with SyncTransport(_config()) as transport:
        assert transport.get("album/123") == "<html>final</html>"


@respx.mock
def test_context_manager_closes_client() -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, text="ok"))
    transport = SyncTransport(_config())
    with transport:
        transport.get("album/123")
    assert transport.is_closed
