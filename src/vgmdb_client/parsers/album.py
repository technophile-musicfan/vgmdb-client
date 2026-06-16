"""Album page parser (clean-room, owned selectors)."""

from __future__ import annotations

import re

import lxml.html
from lxml.html import HtmlElement

from vgmdb_client.models import Album, ArtistRef, Credit, Disc, LocalizedText, Track, normalize_role
from vgmdb_client.parsers import _dom
from vgmdb_client.parsers.errors import ParseError

_ALBUM_ID = re.compile(r"/album/(\d+)")
_BR = re.compile(r"<br\s*/?>", re.IGNORECASE)
_SPLIT_NAMES = re.compile(r"\s*,\s*|\s+and\s+")


def parse_album(html: str) -> Album:
    """Parse a captured vgmdb album page into an :class:`Album` (clean-room selectors)."""
    tree = _dom.parse_tree(html)

    canonical = tree.xpath('//link[@rel="canonical"]/@href')
    match = _ALBUM_ID.search(canonical[0]) if canonical else None
    if match is None:
        raise ParseError("Not a vgmdb album page (no canonical /album/<id>).")
    album_id = int(match.group(1))

    titles = _dom.localized_text(tree.xpath('//h1/span[@class="albumtitle"]'))
    if not titles.all:
        raise ParseError("Album page has no title.")

    info = _info_fields(tree)
    cover_full = _first_url(tree, "medium-media.vgm.io")
    cover_small = _first_url(tree, "thumb-media.vgm.io")

    return Album(
        id=album_id,
        link=canonical[0],
        titles=titles,
        catalog=info.get("Catalog Number"),
        release_date=_dom.partial_date(info.get("Release Date href")) or _dom.partial_date(info.get("Release Date")),
        classification=info.get("Classification"),
        cover_small=cover_small,
        cover_full=cover_full,
        discs=_discs(tree),
        credits=_credits(tree),
        notes=_notes(tree),
    )


def _info_fields(tree: HtmlElement) -> dict[str, str]:
    """Map info-box label -> value text, from the (non-credits) album_infobit table."""
    fields: dict[str, str] = {}
    for table in tree.xpath('//table[@id="album_infobit_large"]'):
        if table.xpath('ancestor::*[@id="collapse_credits"]'):
            continue  # that table holds credits, handled separately
        for row in table.xpath("./tbody/tr | ./tr"):
            label_el = row.xpath('./td[1]//span[@class="label"]')
            if not label_el:
                continue
            label = _dom.text(label_el[0])
            value_td = row.xpath("./td[2]")
            if not value_td:
                continue
            fields[label] = _dom.text(value_td[0])
            href = value_td[0].xpath(".//a/@href")
            if href:
                fields[f"{label} href"] = href[0]
    return fields


def _first_url(tree: HtmlElement, host: str) -> str | None:
    for attr in tree.xpath("//@src | //@href | //@style"):
        if host in attr:
            m = re.search(rf"https?://{re.escape(host)}[^\"' )]+", attr)
            if m:
                return m.group(0)
    return None


def _discs(tree: HtmlElement) -> list[Disc]:
    """Parse discs/tracks from the active tracklist language span(s)."""
    tl_spans = tree.xpath('//*[@id="tracklist"]//span[@class="tl"]')
    if not tl_spans:
        return []
    primary = tl_spans[0]
    discs: list[Disc] = []
    current: Disc | None = None
    tracks: list[Track] = []

    def flush() -> None:
        nonlocal current, tracks
        if current is not None:
            discs.append(current.model_copy(update={"tracks": tracks}))
        tracks = []

    for node in primary.iter():
        if node.tag == "b" and node.text and node.text.strip().lower().startswith("disc"):
            flush()
            num = re.search(r"\d+", node.text)
            current = Disc(number=int(num.group()) if num else None, name=None, tracks=[])
        elif node.tag == "tr" and "rolebit" in (node.get("class") or ""):
            if current is None:
                current = Disc(number=1, name=None, tracks=[])
            tracks.append(_track(node))
    flush()
    if not discs and tracks:
        discs.append(Disc(number=1, name=None, tracks=tracks))
    return discs


def _track(row: HtmlElement) -> Track:
    cells = row.xpath("./td")
    num_el = row.xpath('.//span[@class="label"]')
    number = None
    if num_el:
        n = re.search(r"\d+", _dom.text(num_el[0]))
        number = int(n.group()) if n else None
    time_el = row.xpath('.//span[@class="time"]')
    length = _dom.text(time_el[0]) if time_el else None
    # title cell: the wide colspan cell (no label/time span)
    title = ""
    for cell in cells:
        if cell.xpath('.//span[@class="label"] | .//span[@class="time"]'):
            continue
        title = _dom.text(cell)
        break
    return Track(titles=LocalizedText({"English": title}), number=number, length=length or None)


def _credits(tree: HtmlElement) -> list[Credit]:
    credits: list[Credit] = []
    for row in tree.xpath('//*[@id="collapse_credits"]//tr[@class="maincred"]'):
        label_spans = row.xpath('./td[1]//span[@class="artistname"]')
        role_raw = _dom.text(label_spans[0]) if label_spans else _dom.text(row.xpath("./td[1]")[0])
        value_td = row.xpath("./td[2]")
        if not role_raw or not value_td:
            continue
        artists = _artists(value_td[0])
        credits.append(Credit(role=normalize_role(role_raw), role_raw=role_raw, artists=artists))
    return credits


def _artists(value_td: HtmlElement) -> list[ArtistRef]:
    """Extract artists: linked /artist/ entries, then plain-text names split on ',' / 'and'."""
    artists: list[ArtistRef] = []
    links = value_td.xpath('.//a[contains(@href, "/artist/")]')
    if links:
        for a in links:
            href = a.get("href")
            aid = _ALBUM_ID_ARTIST.search(href)
            spans = a.xpath('.//span[@class="artistname"]')
            names = _dom.localized_text(spans) if spans else LocalizedText({"English": _dom.text(a)})
            artists.append(ArtistRef(names=names, id=int(aid.group(1)) if aid else None, link=_dom.absolute_url(href)))
        return artists
    # no links: split the plain text into individual names
    for name in _SPLIT_NAMES.split(_dom.text(value_td)):
        cleaned = name.strip()
        if cleaned:
            artists.append(ArtistRef(names=LocalizedText({"English": cleaned}), id=None, link=None))
    return artists


_ALBUM_ID_ARTIST = re.compile(r"/artist/(\d+)")


def _notes(tree: HtmlElement) -> str | None:
    nodes = tree.xpath('//*[@id="notes"]')
    if not nodes:
        return None
    raw = lxml.html.tostring(nodes[0], encoding="unicode")
    raw = _BR.sub("\n", raw)
    text = lxml.html.fromstring(raw).text_content().strip()
    return text or None
