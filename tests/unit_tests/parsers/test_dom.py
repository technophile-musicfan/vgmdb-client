"""Tests for parser DOM helpers and ParseError."""

import pytest

from vgmdb_client.errors import VgmdbClientError
from vgmdb_client.models import LocalizedText, PartialDate
from vgmdb_client.parsers import ParseError, _dom


def test_parse_error_is_vgmdb_client_error() -> None:
    assert issubclass(ParseError, VgmdbClientError)
    with pytest.raises(VgmdbClientError, match="boom"):
        raise ParseError("boom")


def test_parse_tree_returns_element() -> None:
    tree = _dom.parse_tree("<html><body><p>hi</p></body></html>")
    assert tree.xpath("//p")[0].text == "hi"


def test_text_collapses_whitespace_and_decodes_entities() -> None:
    tree = _dom.parse_tree("<td>  Original Soundtrack,&nbsp;Vocal \n </td>")
    td = tree.xpath("//td")[0]
    assert _dom.text(td) == "Original Soundtrack, Vocal"


def test_localized_text_english_only_when_placeholder_duplicates() -> None:
    html = (
        '<h1><span class="albumtitle" lang="en">Blossom</span>'
        '<span class="albumtitle" lang="ja"><em> / </em>Blossom</span>'
        '<span class="albumtitle" lang="ja-Latn"><em> / </em>Blossom</span></h1>'
    )
    spans = _dom.parse_tree(html).xpath('//span[@class="albumtitle"]')
    assert _dom.localized_text(spans) == LocalizedText({"English": "Blossom"})


def test_localized_text_keeps_real_japanese_and_distinct_romaji() -> None:
    html = (
        '<h1><span class="albumtitle" lang="en">Akumajo Dracula</span>'
        '<span class="albumtitle" lang="ja"><em> / </em>悪魔城</span>'
        '<span class="albumtitle" lang="ja-Latn"><em> / </em>Akumajo Dracula Fukkoku</span></h1>'
    )
    spans = _dom.parse_tree(html).xpath('//span[@class="albumtitle"]')
    assert _dom.localized_text(spans).all == {
        "English": "Akumajo Dracula",
        "Japanese": "悪魔城",
        "Romaji": "Akumajo Dracula Fukkoku",
    }


def test_partial_date_from_calendar_href() -> None:
    assert _dom.partial_date("/db/calendar.php?year=2005&month=11#20051108") == PartialDate(year=2005, month=11, day=8)


def test_partial_date_year_only_and_unparseable() -> None:
    assert _dom.partial_date("#2002") == PartialDate(year=2002)
    assert _dom.partial_date("nonsense") is None


def test_absolute_url() -> None:
    assert _dom.absolute_url("/artist/137") == "https://vgmdb.net/artist/137"
    assert _dom.absolute_url("https://vgmdb.net/album/4") == "https://vgmdb.net/album/4"
    assert _dom.absolute_url(None) is None
