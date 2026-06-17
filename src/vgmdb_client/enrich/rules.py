"""Deterministic, dependency-free rule-based enrichment backend.

Extracts per-track credits from an album's freeform notes with two conservative patterns — an inline
parenthetical (``<Name> (<ranges>)`` under a role context) and a block pattern (a track-range/number
header line sets the current track set, and following ``<Role> by/: <Names>`` lines attribute to it).
A credit is emitted only with a track context or an inline range, so album-level credits with no
track reference are dropped (precision favored over recall).
"""

from __future__ import annotations

import re

from vgmdb_client.enrich.models import AlbumEnrichment
from vgmdb_client.models import Album, ArtistRef, Credit, LocalizedText, normalize_role

# Role labels we recognize (substring, casefolded). Keeps album-level / non-credit lines out.
_ROLE_KEYWORDS = (
    "compos",
    "arrang",
    "perform",
    "vocal",
    "lyric",
    "words",
    "music",
    "written",
    "sound",
    "mix",
    "master",
    "produc",
    "conduct",
    "guitar",
    "piano",
    "bass",
    "drum",
    "program",
)

# A run of track-range characters (digits, ~ ranges, commas, M / M- / leading-zero prefixes).
_RANGE_TOKEN = re.compile(r"M?-?0*\d+\s*~\s*M?-?0*\d+|M?-?0*\d+", re.I)
# A "<names> (<ranges>)" group: lazy names then a parenthetical.
_INLINE_GROUP = re.compile(r"([^()]*?)\(([^()]+)\)")
# A leading "N." track-number header (e.g. '10. "Glitter Girl"').
_NUMBER_DOT = re.compile(r"^\s*(\d+)\.\s")
# A range header line: optional "Tracks"/"M" lead, then a run of range chars, optional " - title".
_HEADER = re.compile(r"^\s*(?:tracks?\s+)?(M?-?\d[\dM~,\s.-]*?)\s*(?:-\s+\S.*)?$", re.I)
# A role line: "<role> by <names>" or "<role>: <names>".
_ROLE_LINE = re.compile(r"^\s*([^:]{1,40}?)\s+by\s+(.+)$|^\s*([^:]{1,40}?):\s*(.+)$", re.I)
_NAME_SPLIT = re.compile(r"\s*(?:,|;|&|/|\band\b)\s*", re.I)
_WORD = re.compile(r"\w")


def _parse_track_set(text: str) -> set[int]:
    """Parse track-range text into a set of track numbers (``1,4,5`` / ``1~3`` / ``M-01`` / ...)."""
    tracks: set[int] = set()
    for token in _RANGE_TOKEN.findall(text):
        bounds = re.findall(r"\d+", token)
        if not bounds:
            continue
        if "~" in token and len(bounds) >= 2:
            start, end = int(bounds[0]), int(bounds[1])
            if start <= end:
                tracks.update(range(start, end + 1))
        else:
            tracks.add(int(bounds[0]))
    return tracks


def _split_names(text: str) -> list[str]:
    """Split a names blob into individual artist names, keeping only word-bearing entries."""
    return [name for raw in _NAME_SPLIT.split(text) if (name := raw.strip(" ,;&/")) and _WORD.search(name)]


def _has_role_keyword(phrase: str) -> bool:
    folded = phrase.casefold()
    return any(keyword in folded for keyword in _ROLE_KEYWORDS)


def _header_tracks(line: str) -> set[int] | None:
    """Return the track set if ``line`` is a track-range/number header, else ``None``."""
    number_dot = _NUMBER_DOT.match(line)
    if number_dot:
        return {int(number_dot.group(1))}
    match = _HEADER.match(line)
    if not match:
        return None
    tracks = _parse_track_set(match.group(1))
    return tracks or None


def _credit(role_raw: str, names: list[str]) -> Credit:
    role = normalize_role(role_raw)
    artists = [ArtistRef(names=LocalizedText({_name_key(name): name})) for name in names]
    return Credit(role=role, role_raw=role_raw.strip(), artists=artists)


def _name_key(name: str) -> str:
    return "Japanese" if re.search(r"[぀-ヿ㐀-䶿一-鿿]", name) else "English"


def _role_line(line: str) -> tuple[str, str] | None:
    """Return ``(role_phrase, value)`` if ``line`` is a recognized role line, else ``None``."""
    match = _ROLE_LINE.match(line)
    if not match:
        return None
    phrase = match.group(1) or match.group(3)
    value = match.group(2) or match.group(4)
    if phrase and value and _has_role_keyword(phrase):
        return phrase, value
    return None


class RuleBasedBackend:
    """Extract per-track credits from notes with conservative deterministic rules."""

    def enrich(self, album: Album, raw_text: str) -> AlbumEnrichment:
        track_credits: dict[int, list[Credit]] = {}
        current: set[int] | None = None
        for line in raw_text.splitlines():
            if not line.strip():
                current = None
                continue
            header = _header_tracks(line)
            if header is not None:
                current = header
                continue
            role = _role_line(line)
            if role is not None:
                self._emit(track_credits, current, role[0], role[1])

        ordered = {track: track_credits[track] for track in sorted(track_credits)}
        return AlbumEnrichment(album_id=album.id, track_credits=ordered)

    @staticmethod
    def _emit(
        track_credits: dict[int, list[Credit]],
        current: set[int] | None,
        role_phrase: str,
        value: str,
    ) -> None:
        """Emit credits for a role line: inline ``(ranges)`` per name, else the current track set."""

        def add(tracks: set[int], names: list[str]) -> None:
            if not tracks or not names:
                return
            for track in tracks:
                track_credits.setdefault(track, []).append(_credit(role_phrase, names))

        ranged = [(names, _parse_track_set(rng)) for names, rng in _INLINE_GROUP.findall(value)]
        ranged = [(names, tracks) for names, tracks in ranged if tracks]
        if ranged:  # inline parenthetical: names attach to their own ranges
            for names, tracks in ranged:
                add(tracks, _split_names(names))
        elif current is not None:  # block: attribute to the current header's tracks
            add(current, _split_names(value))
