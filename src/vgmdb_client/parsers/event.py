"""Event page parser (clean-room, owned selectors)."""

from __future__ import annotations

import re

from lxml.html import HtmlElement

from vgmdb_client.models import Event, PartialDate
from vgmdb_client.parsers import _dom
from vgmdb_client.parsers.errors import NotAnEventPageError

_EVENT_ID = re.compile(r"/event/(\d+)")


def parse_event(html: str) -> Event:
    """Parse a captured vgmdb event page into an :class:`Event` (clean-room selectors)."""
    tree = _dom.parse_tree(html)

    canonical = tree.xpath('//link[@rel="canonical"]/@href')
    match = _EVENT_ID.search(canonical[0]) if canonical else None
    if match is None:
        raise NotAnEventPageError()

    # No <h1> on event pages; the event's own name is the leading group of albumtitle spans
    # (the page also lists related-album titles in the same class).
    names = _dom.localized_text(_leading_group(tree.xpath('//span[@class="albumtitle"]')))
    if not names.all:
        raise NotAnEventPageError()

    return Event(
        id=int(match.group(1)),
        link=canonical[0],
        names=names,
        type=None,
        start_date=_event_date(tree),
        end_date=None,
        notes=None,
    )


def _leading_group(spans: list[HtmlElement]) -> list[HtmlElement]:
    """The first contiguous run of language spans (one per lang) — the event's own name."""
    seen: set[str] = set()
    group: list[HtmlElement] = []
    for span in spans:
        lang = span.get("lang")
        if lang and lang in seen:
            break
        if lang:
            seen.add(lang)
        group.append(span)
    return group


def _event_date(tree: HtmlElement) -> PartialDate | None:
    """The event's date from the header's ``smallfont label`` (the lone such label on the page)."""
    labels = tree.xpath('//span[@class="smallfont label"]')
    return _dom.partial_date(_dom.text(labels[0])) if labels else None
