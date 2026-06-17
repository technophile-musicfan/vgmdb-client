"""parse_artist validated against the captured golden fixtures."""

import pytest

from tests.support.fixtures import iter_artist_fixtures, load_artist_fixture
from vgmdb_client.parsers import parse_artist
from vgmdb_client.parsers.errors import NotAnArtistPageError


@pytest.mark.parametrize("artist_id", sorted(iter_artist_fixtures()))
def test_parse_artist_matches_golden(artist_id: int) -> None:
    html, golden = load_artist_fixture(artist_id)
    assert parse_artist(html) == golden


def test_parse_artist_raises_on_non_artist_page() -> None:
    with pytest.raises(NotAnArtistPageError):
        parse_artist("<html><body><h1>Just a moment...</h1></body></html>")
