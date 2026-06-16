"""Album page parser (clean-room, owned selectors)."""

from __future__ import annotations

import re

import lxml.html
from lxml.html import HtmlElement

from vgmdb_client.models import Album, ArtistRef, Credit, Disc, LocalizedText, Track, normalize_role
from vgmdb_client.parsers import _dom
from vgmdb_client.parsers.errors import NotAnAlbumPageError

_ALBUM_ID = re.compile(r"/album/(\d+)")
_BR = re.compile(r"<br\s*/?>", re.IGNORECASE)
_TAB_PAREN = re.compile(r"\s*\(.*\)\s*$")
_WORD = re.compile(r"\w")


def parse_album(html: str) -> Album:
    """Parse a captured vgmdb album page into an :class:`Album` (clean-room selectors)."""
    tree = _dom.parse_tree(html)

    canonical = tree.xpath('//link[@rel="canonical"]/@href')
    match = _ALBUM_ID.search(canonical[0]) if canonical else None
    if match is None:
        raise NotAnAlbumPageError()
    album_id = int(match.group(1))

    titles = _dom.localized_text(tree.xpath('//h1/span[@class="albumtitle"]'))
    if not titles.all:
        raise NotAnAlbumPageError()

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
            fields[label] = _value_text(value_td[0])
            href = value_td[0].xpath(".//a/@href")
            if href:
                fields[f"{label} href"] = href[0]
    return fields


def _value_text(td: HtmlElement) -> str:
    """Text of an info-box value cell, excluding script blocks and child-menu popups."""
    parts = td.xpath('.//text()[not(ancestor::script) and not(ancestor::div[contains(@class, "vbmenu_popup")])]')
    return " ".join(" ".join(parts).split())


def _first_url(tree: HtmlElement, host: str) -> str | None:
    for attr in tree.xpath("//@src | //@href | //@style"):
        if host in attr:
            m = re.search(rf"https?://{re.escape(host)}[^\"' )]+", attr)
            if m:
                return m.group(0)
    return None


# A parsed track row: (number, length, title_text). Discs: (number, name, list[_RawTrack]).
_RawTrack = tuple[int | None, str | None, str]
_RawDisc = tuple[int | None, str | None, list[_RawTrack]]


def _discs(tree: HtmlElement) -> list[Disc]:
    """Parse discs/tracks, merging per-language tracklist tabs into multi-language titles."""
    per_lang, primary_label = _language_tracklists(tree)
    structure = per_lang[primary_label] if primary_label else []
    discs: list[Disc] = []
    for di, (number, name, raw_tracks) in enumerate(structure):
        tracks: list[Track] = []
        for ti, (tnum, tlen, _title) in enumerate(raw_tracks):
            values: dict[str, str] = {}
            for label, lang_discs in per_lang.items():
                if di < len(lang_discs) and ti < len(lang_discs[di][2]):
                    values[label] = lang_discs[di][2][ti][2]
            tracks.append(Track(titles=_dom.localized_from_labels(values), number=tnum, length=tlen or None))
        discs.append(Disc(number=number, name=name, tracks=tracks))
    return discs


def _language_tracklists(tree: HtmlElement) -> tuple[dict[str, list[_RawDisc]], str | None]:
    """Parse each language tracklist tab, preferring the canonical (non-parenthetical) tab.

    Returns ``(per_language_discs, primary_label)``. When two tabs share a label (e.g. "English"
    and "English (unofficial)"), the canonical one wins and the other is ignored.
    """
    tl_spans = tree.xpath('//*[@id="tracklist"]//span[@class="tl"]')
    if not tl_spans:
        return {}, None

    lang_raw = {
        a.get("rel"): _dom.text(a)
        for a in tree.xpath('//ul[contains(@class, "tabnav")]//a[@rel]')
        if (a.get("rel") or "").startswith("tl")
    }
    per_lang: dict[str, list[_RawDisc]] = {}
    canonical: set[str] = set()
    primary_label: str | None = None
    for span in tl_spans:
        raw = lang_raw.get(span.get("id"), "English")
        label = _TAB_PAREN.sub("", raw).strip()
        is_canonical = "(" not in raw
        if primary_label is None and is_canonical:
            primary_label = label
        if label in per_lang and (not is_canonical or label in canonical):
            continue
        per_lang[label] = _parse_tl(span)
        if is_canonical:
            canonical.add(label)
    return per_lang, primary_label or next(iter(per_lang), None)


def _parse_tl(span: HtmlElement) -> list[_RawDisc]:
    """Parse one language tracklist span into (disc_number, [(number, length, title)]) groups."""
    discs: list[_RawDisc] = []
    number: int | None = None
    name: str | None = None
    tracks: list[_RawTrack] = []
    started = False

    def flush() -> None:
        nonlocal tracks
        if started:
            discs.append((number, name, tracks))
        tracks = []

    for node in span.iter():
        if node.tag == "b" and node.text and node.text.strip().lower().startswith("disc"):
            flush()
            started = True
            name = _dom.text(node)
            m = re.search(r"\d+", node.text)
            number = int(m.group()) if m else None
        elif node.tag == "tr" and "rolebit" in (node.get("class") or ""):
            tracks.append(_raw_track(node))
    flush()
    if not discs and tracks:
        discs.append((1, None, tracks))
    return discs


def _raw_track(row: HtmlElement) -> _RawTrack:
    num_el = row.xpath('.//span[@class="label"]')
    number = None
    if num_el:
        m = re.search(r"\d+", _dom.text(num_el[0]))
        number = int(m.group()) if m else None
    time_el = row.xpath('.//span[@class="time"]')
    length = _dom.text(time_el[0]) if time_el else None
    # The title lives in the wide cell (width="100%"/colspan); it may itself wrap the text in a
    # span.label (e.g. the "(no title available)" placeholder), so select by width, not by spans.
    title = ""
    wide = row.xpath('./td[@width="100%"] | ./td[@colspan]')
    if wide:
        title = _dom.text(wide[0])
    return number, length, title


def _credits(tree: HtmlElement) -> list[Credit]:
    result: list[Credit] = []
    for row in tree.xpath('//*[@id="collapse_credits"]//tr[@class="maincred"]'):
        label_spans = row.xpath('./td[1]//span[@class="artistname"]')
        role_raw = _dom.text(label_spans[0]) if label_spans else _dom.text(row.xpath("./td[1]")[0])
        value_td = row.xpath("./td[2]")
        if not role_raw or not value_td:
            continue
        artists = _artists(value_td[0])
        result.append(Credit(role=normalize_role(role_raw), role_raw=role_raw, artists=artists))
    return result


def _artists(value_td: HtmlElement) -> list[ArtistRef]:
    """Extract the artists in a credit value cell, in document order.

    Walks the cell as an ordered stream of text runs and ``/artist/`` links. Linked artists are
    kept verbatim (with their localized names + id/link). Plain-text runs are split into names on
    a *list comma* — a comma NOT preceded by whitespace — so a ``"Studio , City"`` venue stays
    whole while ``"A, B, C"`` splits; ``" and "`` is never a separator. A trailing ``(affiliation)``
    is stripped from each name. A linked artist enclosed in parentheses right after another (e.g.
    ``"Syrufit (hiro.na)"``) is a parenthetical/aka and is dropped — the parens are in the markup,
    so this is a structural rule, not a semantic one.
    """
    artists: list[ArtistRef] = []

    def emit_text(run: str) -> None:
        for raw in _LIST_COMMA.split(run):
            name = _TRAILING_PAREN.sub("", raw.strip(" ,")).strip(" ,")
            if name and _WORD.search(name):  # skip stray punctuation (e.g. parens around a link)
                key = "Japanese" if _dom.has_cjk(name) else "English"
                artists.append(ArtistRef(names=LocalizedText({key: name}), id=None, link=None))

    prev_text = value_td.text or ""
    emit_text(prev_text)
    for child in value_td:
        href = child.get("href")
        tail = child.tail or ""
        if child.tag == "a" and href and "/artist/" in href:
            parenthetical = prev_text.rstrip().endswith("(") and tail.lstrip().startswith(")")
            if not parenthetical:
                aid = _ARTIST_ID.search(href)
                spans = child.xpath('.//span[@class="artistname"]')
                names = _dom.localized_text(spans) if spans else LocalizedText({"English": _dom.text(child)})
                artists.append(
                    ArtistRef(names=names, id=int(aid.group(1)) if aid else None, link=_dom.absolute_url(href))
                )
        else:
            emit_text(child.text_content())
        emit_text(tail)
        prev_text = tail
    return artists


_ARTIST_ID = re.compile(r"/artist/(\d+)")
_LIST_COMMA = re.compile(r"(?<=\S),\s*")
_TRAILING_PAREN = re.compile(r"\s*\([^)]*\)$")


def _notes(tree: HtmlElement) -> str | None:
    nodes = tree.xpath('//*[@id="notes"]')
    if not nodes:
        return None
    raw = lxml.html.tostring(nodes[0], encoding="unicode")
    raw = _BR.sub("\n", raw)
    text = lxml.html.fromstring(raw).text_content().strip()
    return text or None
