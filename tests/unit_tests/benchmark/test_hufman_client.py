"""Tests for the optional hufman HTTP client (no live service; respx-mocked)."""

from __future__ import annotations

import httpx
import pytest
import respx

from benchmarks.quality.hufman_client import fetch_album, hufman_base_url

BASE = "http://hufman.test"


@respx.mock
def test_fetch_album_returns_dict_on_success() -> None:
    respx.get(f"{BASE}/album/271").mock(return_value=httpx.Response(200, json={"name": "X"}))
    data = fetch_album(271, base_url=BASE)
    assert data == {"name": "X"}


@respx.mock
def test_fetch_album_unreachable_returns_none() -> None:
    respx.get(f"{BASE}/album/271").mock(side_effect=httpx.ConnectError("down"))
    assert fetch_album(271, base_url=BASE) is None


@respx.mock
def test_fetch_album_http_error_returns_none() -> None:
    respx.get(f"{BASE}/album/271").mock(return_value=httpx.Response(500))
    assert fetch_album(271, base_url=BASE) is None


@respx.mock
def test_fetch_album_non_object_returns_none() -> None:
    respx.get(f"{BASE}/album/271").mock(return_value=httpx.Response(200, json=["not", "a", "dict"]))
    assert fetch_album(271, base_url=BASE) is None


def test_base_url_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HUFMAN_URL", raising=False)
    assert hufman_base_url() == "http://localhost:5000"
    monkeypatch.setenv("HUFMAN_URL", BASE)
    assert hufman_base_url() == BASE
