"""Search results page parser (clean-room, owned selectors)."""

from __future__ import annotations

import re

from lxml.html import HtmlElement

from vgmdb_client.models import AlbumSearchResult, SearchResults
from vgmdb_client.parsers import _dom
from vgmdb_client.parsers.errors import NotASearchPageError

_ALBUM_ID = re.compile(r"/album/(\d+)")
_QUERY = re.compile(r'results for "(.*)"\s*$')


def parse_search(html: str) -> SearchResults:
    """Parse a captured vgmdb search-results page into :class:`SearchResults`."""
    tree = _dom.parse_tree(html)

    container = tree.xpath('//*[@id="albumresults"]')
    if not container:
        raise NotASearchPageError()

    query = _query(tree)
    albums = [_result_row(row) for row in container[0].xpath('.//table[contains(@class, "results")]//tr[@rel]')]
    return SearchResults(query=query, albums=[a for a in albums if a is not None])


def _query(tree: HtmlElement) -> str:
    """The searched query, read from the 'N album results for "<query>"' header."""
    for h3 in tree.xpath('//h3[@class="label"]'):
        text = _dom.text(h3)
        if "album results for" in text:
            match = _QUERY.search(text)
            if match:
                return match.group(1)
    return ""


def _result_row(row: HtmlElement) -> AlbumSearchResult | None:
    link_el = row.xpath('.//a[contains(@href, "/album/")]')
    if not link_el:
        return None
    match = _ALBUM_ID.search(link_el[0].get("href"))
    if match is None:
        return None
    album_id = int(match.group(1))

    titles = _dom.localized_text(link_el[0].xpath('.//span[@class="albumtitle"]'))
    catalog_el = row.xpath('.//span[contains(@class, "catalog")]')
    catalog = _dom.text(catalog_el[0]) if catalog_el else None
    if catalog in ("", "N/A"):
        catalog = None

    # Find the release-date cell, skipping the catalog and title cells so a numeric catalog
    # (e.g. "3939") can't be mistaken for a year.
    release_date = None
    for cell in row.xpath("./td"):
        if cell.xpath('.//span[contains(@class, "catalog")] | .//a[contains(@href, "/album/")]'):
            continue
        parsed = _dom.partial_date(_dom.text(cell))
        if parsed is not None:
            release_date = parsed
            break

    return AlbumSearchResult(
        id=album_id,
        link=_dom.absolute_url(f"/album/{album_id}"),
        titles=titles,
        catalog=catalog,
        release_date=release_date,
    )
