"""Tests for search models (AlbumSearchResult, SearchResults)."""

from vgmdb_client.models.common import LocalizedText, PartialDate
from vgmdb_client.models.search import AlbumSearchResult, SearchResults


def _titles(**langs: str) -> LocalizedText:
    return LocalizedText(langs)


def test_album_search_result_construction_and_defaults() -> None:
    result = AlbumSearchResult(
        id=123,
        link="album/123",
        titles=_titles(English="NieR OST"),
        catalog="SQEX-10165",
        release_date=PartialDate(year=2010),
    )
    assert result.id == 123
    assert result.titles.prefer("English") == "NieR OST"

    bare = AlbumSearchResult(id=1, titles=_titles(English="Minimal"))
    assert bare.link is None
    assert bare.catalog is None
    assert bare.release_date is None


def test_search_results_carry_query_and_albums() -> None:
    results = SearchResults(
        query="nier",
        albums=[AlbumSearchResult(id=123, titles=_titles(English="NieR OST"))],
    )
    assert results.query == "nier"
    assert len(results.albums) == 1
    assert results.albums[0].id == 123


def test_search_results_albums_default_empty() -> None:
    assert SearchResults(query="empty").albums == []
