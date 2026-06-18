"""Tests for the event page parser and the album release_event extraction."""

from __future__ import annotations

import pytest

from tests.support.fixtures import load_album_fixture, load_event_fixture
from vgmdb_client.parsers import parse_album, parse_event
from vgmdb_client.parsers.errors import NotAnEventPageError


def test_parse_event_matches_golden() -> None:
    html, golden = load_event_fixture(149)
    assert parse_event(html) == golden


def test_parse_event_rejects_non_event_page() -> None:
    with pytest.raises(NotAnEventPageError):
        parse_event("<html><body><h1>nope</h1></body></html>")


def test_album_with_release_event() -> None:
    html, golden = load_album_fixture(33000)
    album = parse_album(html)
    assert album.release_event is not None
    assert album.release_event.id == 149
    assert album.release_event.link == "https://vgmdb.net/event/149"
    assert album == golden


def test_album_without_release_event_is_none() -> None:
    html, _ = load_album_fixture(271)
    assert parse_album(html).release_event is None
