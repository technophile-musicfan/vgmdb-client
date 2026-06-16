"""Tests for the shared client path builders."""

from vgmdb_client.client import _core


def test_album_path() -> None:
    assert _core.album_path(271) == "/album/271"


def test_search_path_encodes_query() -> None:
    assert _core.search_path("final fantasy") == "/search?q=final+fantasy"
    assert _core.search_path("final, fantasy") == "/search?q=final%2C+fantasy"
