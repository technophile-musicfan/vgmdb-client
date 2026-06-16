"""Shared lxml helpers for the parsers (pure, no I/O)."""

from __future__ import annotations

import re

import lxml.html
from lxml.html import HtmlElement

from vgmdb_client.models import LocalizedText, PartialDate

_BASE = "https://vgmdb.net"
_CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿＀-￯]")
_DATE_FRAGMENT = re.compile(r"#(\d{4})(\d{2})?(\d{2})?$")
_DATE_QUERY = re.compile(r"year=(\d{4})(?:&month=(\d{1,2}))?(?:&day=(\d{1,2}))?")
_LEADING_SLASH = re.compile(r"^/\s*")


def has_cjk(value: str) -> bool:
    """True if the string contains real Japanese/CJK script."""
    return bool(_CJK.search(value))


def parse_tree(html: str) -> HtmlElement:
    """Parse an HTML document into an lxml element tree."""
    return lxml.html.fromstring(html)


def text(element: HtmlElement | None) -> str:
    """Whitespace-collapsed text content of an element (entities decoded by lxml)."""
    if element is None:
        return ""
    return " ".join(element.text_content().split())


def _span_text(span: HtmlElement) -> str:
    # Placeholder language spans render a leading "<em> / </em>"; text_content drops the <em>,
    # leaving a leading "/ " — strip a single leading slash separator.
    return _LEADING_SLASH.sub("", text(span)).strip()


def _placeholder_rule(english: str, japanese: str | None, romaji: str | None) -> LocalizedText:
    """Apply the multi-language placeholder rule shared by both title sources.

    English is kept when present; Japanese only when it contains real Japanese script; Romaji
    only when it differs from the English text. Placeholder duplicates are dropped.
    """
    out: dict[str, str] = {}
    if english:
        out["English"] = english
    if japanese and _CJK.search(japanese):
        out["Japanese"] = japanese
    if romaji and romaji != english:
        out["Romaji"] = romaji
    return LocalizedText(out)


def localized_text(spans: list[HtmlElement]) -> LocalizedText:
    """Build :class:`LocalizedText` from language spans (lang attributes en/ja/ja-Latn)."""
    by_lang = {span.get("lang"): _span_text(span) for span in spans if span.get("lang")}
    return _placeholder_rule(by_lang.get("en", ""), by_lang.get("ja"), by_lang.get("ja-Latn"))


def localized_from_labels(values: dict[str, str]) -> LocalizedText:
    """Build :class:`LocalizedText` from already-labelled values (keys English/Japanese/Romaji)."""
    return _placeholder_rule(values.get("English", ""), values.get("Japanese"), values.get("Romaji"))


def partial_date(href_or_text: str | None) -> PartialDate | None:
    """Parse a vgmdb date: prefer the ``#YYYYMMDD`` calendar fragment, else ``PartialDate.parse``."""
    if not href_or_text:
        return None
    match = _DATE_FRAGMENT.search(href_or_text) or _DATE_QUERY.search(href_or_text)
    if match:
        year = int(match.group(1))
        month = int(match.group(2)) if match.group(2) else None
        day = int(match.group(3)) if match.group(3) else None
        try:
            return PartialDate(year=year, month=month, day=day)
        except ValueError:
            return None
    return PartialDate.parse(href_or_text) or _parse_text_date(href_or_text)


_MONTHS = {
    m: i
    for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)
}
_TEXT_DATE = re.compile(r"^([A-Za-z]{3})[a-z]*(?:\s+(\d{1,2}),)?\s+(\d{4})$")
_YEAR_ONLY = re.compile(r"^(\d{4})$")


def _parse_text_date(text: str) -> PartialDate | None:
    """Parse human date text: 'Mon DD, YYYY', 'Mon YYYY', or 'YYYY'."""
    value = text.strip()
    year_only = _YEAR_ONLY.match(value)
    if year_only:
        return PartialDate(year=int(year_only.group(1)))
    match = _TEXT_DATE.match(value)
    if not match:
        return None
    month = _MONTHS.get(match.group(1).lower())
    if month is None:
        return None
    day = int(match.group(2)) if match.group(2) else None
    try:
        return PartialDate(year=int(match.group(3)), month=month, day=day)
    except ValueError:
        return None


def absolute_url(href: str | None) -> str | None:
    """Make a vgmdb-relative href absolute; pass through absolute URLs; ``None`` -> ``None``."""
    if not href:
        return None
    if href.startswith(("http://", "https://")):
        return href
    return _BASE + href if href.startswith("/") else f"{_BASE}/{href}"
