"""Shared lxml helpers for the parsers (pure, no I/O)."""

from __future__ import annotations

import re

import lxml.html
from lxml.html import HtmlElement

from vgmdb_client.models import LocalizedText, PartialDate

_BASE = "https://vgmdb.net"
_LANG_LABELS = {"en": "English", "ja": "Japanese", "ja-Latn": "Romaji"}
_CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿＀-￯]")
_DATE_FRAGMENT = re.compile(r"#(\d{4})(\d{2})?(\d{2})?$")
_LEADING_SLASH = re.compile(r"^/\s*")


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


def localized_text(spans: list[HtmlElement]) -> LocalizedText:
    """Build :class:`LocalizedText` from language spans, applying the placeholder rule.

    ``en`` -> English; ``ja`` -> Japanese only when it contains real Japanese script;
    ``ja-Latn`` -> Romaji only when it differs from the English text. Placeholder
    duplicates (other-language spans that merely echo the English Latin text) are dropped.
    """
    by_lang = {span.get("lang"): _span_text(span) for span in spans if span.get("lang")}
    english = by_lang.get("en", "")
    out: dict[str, str] = {}
    if english:
        out["English"] = english
    japanese = by_lang.get("ja")
    if japanese and _CJK.search(japanese):
        out["Japanese"] = japanese
    romaji = by_lang.get("ja-Latn")
    if romaji and romaji != english:
        out["Romaji"] = romaji
    return LocalizedText(out)


def localized_from_labels(values: dict[str, str]) -> LocalizedText:
    """Build :class:`LocalizedText` from already-labelled values, applying the placeholder rule.

    Keys are the display labels ("English"/"Japanese"/"Romaji"). English is kept when present;
    Japanese only when it contains real Japanese script; Romaji only when it differs from English.
    """
    english = values.get("English", "")
    out: dict[str, str] = {}
    if english:
        out["English"] = english
    japanese = values.get("Japanese")
    if japanese and _CJK.search(japanese):
        out["Japanese"] = japanese
    romaji = values.get("Romaji")
    if romaji and romaji != english:
        out["Romaji"] = romaji
    return LocalizedText(out)


def partial_date(href_or_text: str | None) -> PartialDate | None:
    """Parse a vgmdb date: prefer the ``#YYYYMMDD`` calendar fragment, else ``PartialDate.parse``."""
    if not href_or_text:
        return None
    match = _DATE_FRAGMENT.search(href_or_text)
    if match:
        year = int(match.group(1))
        month = int(match.group(2)) if match.group(2) else None
        day = int(match.group(3)) if match.group(3) else None
        try:
            return PartialDate(year=year, month=month, day=day)
        except ValueError:
            return None
    return PartialDate.parse(href_or_text)


def absolute_url(href: str | None) -> str | None:
    """Make a vgmdb-relative href absolute; pass through absolute URLs; ``None`` -> ``None``."""
    if not href:
        return None
    if href.startswith(("http://", "https://")):
        return href
    return _BASE + href if href.startswith("/") else f"{_BASE}/{href}"
