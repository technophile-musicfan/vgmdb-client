"""Product page parser (clean-room, owned selectors)."""

from __future__ import annotations

import re

from lxml.html import HtmlElement

from vgmdb_client.models import LocalizedText, OrgRef, Product, ProductRef
from vgmdb_client.parsers import _dom
from vgmdb_client.parsers.errors import NotAProductPageError

_PRODUCT_ID = re.compile(r"/product/(\d+)")
_ORG_ID = re.compile(r"/org/(\d+)")
# Organization links live in these definition-list fields; their refs are merged + deduped.
_ORG_FIELDS = ("Developer", "Publisher")


def parse_product(html: str) -> Product:
    """Parse a captured vgmdb product page into a :class:`Product` (clean-room selectors)."""
    tree = _dom.parse_tree(html)

    canonical = tree.xpath('//link[@rel="canonical"]/@href')
    match = _PRODUCT_ID.search(canonical[0]) if canonical else None
    if match is None:
        raise NotAProductPageError()

    names = _dom.localized_text(_leading_group(tree.xpath('//span[@class="albumtitle"]')))
    if not names.all:
        raise NotAProductPageError()

    return Product(
        id=int(match.group(1)),
        link=canonical[0],
        names=names,
        type=None,
        notes=None,
        franchises=_franchises(tree),
        organizations=_organizations(tree),
    )


def _leading_group(spans: list[HtmlElement]) -> list[HtmlElement]:
    """The first contiguous run of language spans (one per lang) — the entity's own name.

    The header's title spans precede later ``albumtitle`` spans (e.g. a franchise value), so the run
    up to the first repeated ``lang`` is the product's own multi-language name.
    """
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


def _franchises(tree: HtmlElement) -> list[ProductRef]:
    dd = _dom.dd_for_label(tree, "Franchises")
    if dd is None:
        return []
    refs: list[ProductRef] = []
    for anchor in dd.xpath('.//a[contains(@href, "/product/")]'):
        href = anchor.get("href")
        pid = _PRODUCT_ID.search(href or "")
        names = _ref_names(anchor)
        if names.all:
            refs.append(ProductRef(names=names, id=int(pid.group(1)) if pid else None, link=_ref_link(href)))
    return refs


def _organizations(tree: HtmlElement) -> list[OrgRef]:
    """Org refs from the Developer + Publisher fields, deduped by id in document order."""
    refs: list[OrgRef] = []
    seen: set[int] = set()
    for label in _ORG_FIELDS:
        dd = _dom.dd_for_label(tree, label)
        if dd is None:
            continue
        for anchor in dd.xpath('.//a[contains(@href, "/org/")]'):
            href = anchor.get("href")
            oid_match = _ORG_ID.search(href or "")
            oid = int(oid_match.group(1)) if oid_match else None
            if oid is not None and oid in seen:
                continue
            names = _ref_names(anchor)
            if not names.all:
                continue
            if oid is not None:
                seen.add(oid)
            refs.append(OrgRef(names=names, id=oid, link=_ref_link(href)))
    return refs


def _ref_names(anchor: HtmlElement) -> LocalizedText:
    """Localized names from an entity link's ``productname`` language spans."""
    spans = anchor.xpath('.//span[@class="productname"]')
    if spans:
        return _dom.localized_text(_leading_group(spans))
    return LocalizedText({"English": _dom.text(anchor)})


def _ref_link(href: str | None) -> str | None:
    """Absolute ref link with any query string (e.g. ``?tab=products``) stripped."""
    if not href:
        return None
    return _dom.absolute_url(href.split("?", 1)[0])
