"""parse_album validated against the M5 golden fixtures."""

import pytest

from tests.support.fixtures import iter_album_fixtures, load_album_fixture
from vgmdb_client.parsers import ParseError, parse_album


@pytest.mark.parametrize("album_id", sorted(iter_album_fixtures()))
def test_parse_album_matches_golden(album_id: int) -> None:
    html, golden = load_album_fixture(album_id)
    assert parse_album(html) == golden


def test_parse_album_raises_on_non_album_page() -> None:
    with pytest.raises(ParseError):
        parse_album("<html><body><h1>Just a moment...</h1></body></html>")
