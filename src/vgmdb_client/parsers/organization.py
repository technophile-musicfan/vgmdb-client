"""Organization page parser (clean-room, owned selectors)."""

from __future__ import annotations

import re

from lxml.html import HtmlElement

from vgmdb_client.models import LocalizedText, Organization
from vgmdb_client.parsers import _dom
from vgmdb_client.parsers.errors import NotAnOrganizationPageError

_ORG_ID = re.compile(r"/org/(\d+)")


def parse_organization(html: str) -> Organization:
    """Parse a captured vgmdb organization page into an :class:`Organization` (clean-room selectors)."""
    tree = _dom.parse_tree(html)

    canonical = tree.xpath('//link[@rel="canonical"]/@href')
    match = _ORG_ID.search(canonical[0]) if canonical else None
    if match is None:
        raise NotAnOrganizationPageError()

    names = _name(tree)
    if not names.all:
        raise NotAnOrganizationPageError()

    return Organization(
        id=int(match.group(1)),
        link=canonical[0],
        names=names,
        type=_field_text(tree, "Type"),
        notes=_field_text(tree, "Description"),
    )


def _name(tree: HtmlElement) -> LocalizedText:
    """The organization's display name from the page heading."""
    headings = [_dom.text(h) for h in tree.xpath("//h1")]
    name = next((h for h in headings if h), "")
    if not name:
        return LocalizedText({})
    key = "Japanese" if _dom.has_cjk(name) else "English"
    return LocalizedText({key: name})


def _field_text(tree: HtmlElement, label: str) -> str | None:
    """The text of a ``<dt class="label">`` info field's ``<dd>``, or ``None`` if absent/empty."""
    dd = _dom.dd_for_label(tree, label)
    if dd is None:
        return None
    return _dom.text(dd) or None
