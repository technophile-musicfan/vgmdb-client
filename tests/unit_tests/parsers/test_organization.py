"""parse_organization validated against the captured golden fixtures."""

import pytest

from tests.support.fixtures import iter_organization_fixtures, load_organization_fixture
from vgmdb_client.parsers import parse_organization
from vgmdb_client.parsers.errors import NotAnOrganizationPageError


@pytest.mark.parametrize("org_id", sorted(iter_organization_fixtures()))
def test_parse_organization_matches_golden(org_id: int) -> None:
    html, golden = load_organization_fixture(org_id)
    assert parse_organization(html) == golden


def test_parse_organization_raises_on_non_org_page() -> None:
    with pytest.raises(NotAnOrganizationPageError):
        parse_organization("<html><body><h1>Just a moment...</h1></body></html>")
