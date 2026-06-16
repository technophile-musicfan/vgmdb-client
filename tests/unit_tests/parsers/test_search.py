"""parse_search validated against the M5 search fixtures."""

import pytest

from tests.support.fixtures import load_search_fixture
from vgmdb_client.parsers import ParseError, parse_search


def test_parse_search_near_empty() -> None:
    html, golden = load_search_fixture("near-empty")
    result = parse_search(html)
    assert result.query == golden.query
    assert result.albums == []


def test_parse_search_multi_hit_first_10() -> None:
    # The golden is a first-10 sample (manifest golden_scope: "first-10").
    html, golden = load_search_fixture("multi-hit")
    result = parse_search(html)
    assert result.query == golden.query
    assert result.albums[:10] == golden.albums


def test_parse_search_raises_on_non_search_page() -> None:
    with pytest.raises(ParseError):
        parse_search("<html><body><h1>Some album</h1></body></html>")
