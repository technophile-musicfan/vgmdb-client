"""Artist page parser (clean-room, owned selectors)."""

from __future__ import annotations

import re

from lxml.html import HtmlElement

from vgmdb_client.models import Artist, ArtistRef, LocalizedText
from vgmdb_client.parsers import _dom
from vgmdb_client.parsers.errors import NotAnArtistPageError

_ARTIST_ID = re.compile(r"/artist/(\d+)")
# vgmdb info-field labels render as <b style="color: #788990">Label</b>.
_INFO_LABEL_COLOR = "788990"


def parse_artist(html: str) -> Artist:
    """Parse a captured vgmdb artist page into an :class:`Artist` (clean-room selectors)."""
    tree = _dom.parse_tree(html)

    canonical = tree.xpath('//link[@rel="canonical"]/@href')
    match = _ARTIST_ID.search(canonical[0]) if canonical else None
    if match is None:
        raise NotAnArtistPageError()
    artist_id = int(match.group(1))

    names = _name(tree)
    if not names.all:
        raise NotAnArtistPageError()

    fields = _info_fields(tree)
    return Artist(
        id=artist_id,
        link=canonical[0],
        names=names,
        aliases=_aliases(fields.get("Aliases")),
        type=None,
        birthdate=_dom.partial_date(_field_text(fields.get("Birthdate"), "Birthdate")),
        notes=None,
        members=_refs(fields.get("Members")),
        units=_refs(fields.get("Units")),
    )


def _name(tree: HtmlElement) -> LocalizedText:
    """The artist's display name from the header (the large styled span in #innermain)."""
    spans = tree.xpath('//*[@id="innermain"]/span[contains(@style, "1.5em")]')
    name = _dom.text(spans[0]) if spans else ""
    if not name:
        return LocalizedText({})
    key = "Japanese" if _dom.has_cjk(name) else "English"
    return LocalizedText({key: name})


def _info_fields(tree: HtmlElement) -> dict[str, HtmlElement]:
    """Map info-field label -> the enclosing div, for each ``<b>`` profile label."""
    fields: dict[str, HtmlElement] = {}
    for label_el in tree.xpath(f'//b[contains(@style, "{_INFO_LABEL_COLOR}")]'):
        label = _dom.text(label_el)
        parent = label_el.getparent()
        if label and parent is not None and label not in fields:
            fields[label] = parent
    return fields


def _field_text(div: HtmlElement | None, label: str) -> str | None:
    """The value text of an info field (the div's text with the leading label removed)."""
    if div is None:
        return None
    full = _dom.text(div)
    value = full[len(label) :].strip() if full.startswith(label) else full
    return value or None


def _aliases(div: HtmlElement | None) -> list[str]:
    """Alias names: one per inner ``<div>`` in the Aliases field."""
    if div is None:
        return []
    aliases = [_dom.text(inner) for inner in div.xpath("./div")]
    return [alias for alias in aliases if alias]


def _refs(div: HtmlElement | None) -> list[ArtistRef]:
    """Artist refs from a field's ``/artist/`` links (e.g. Members, Units), in document order."""
    if div is None:
        return []
    refs: list[ArtistRef] = []
    for anchor in div.xpath('.//a[contains(@href, "/artist/")]'):
        href = anchor.get("href")
        aid = _ARTIST_ID.search(href or "")
        spans = anchor.xpath('.//span[@class="artistname"]')
        names = _dom.localized_text(spans) if spans else LocalizedText({"English": _dom.text(anchor)})
        if names.all:
            refs.append(ArtistRef(names=names, id=int(aid.group(1)) if aid else None, link=_dom.absolute_url(href)))
    return refs
