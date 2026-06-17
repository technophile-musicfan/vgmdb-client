"""parse_product validated against the captured golden fixtures."""

import pytest

from tests.support.fixtures import iter_product_fixtures, load_product_fixture
from vgmdb_client.parsers import parse_product
from vgmdb_client.parsers.errors import NotAProductPageError


def test_product_fixtures_present() -> None:
    # Guard against the parametrized test below silently collecting zero cases.
    assert list(iter_product_fixtures())


@pytest.mark.parametrize("product_id", sorted(iter_product_fixtures()))
def test_parse_product_matches_golden(product_id: int) -> None:
    html, golden = load_product_fixture(product_id)
    assert parse_product(html) == golden


def test_parse_product_raises_on_non_product_page() -> None:
    with pytest.raises(NotAProductPageError):
        parse_product("<html><body><h1>Just a moment...</h1></body></html>")
