"""Normalized credit-role vocabulary and the mapping from freeform vgmdb labels.

vgmdb credit labels are freeform (e.g. "Original Music Composed by", "Mastering Studio").
``normalize_role`` maps them to a small controlled vocabulary; the verbatim label is kept
separately on ``Credit.role_raw``. Mapping is conservative: anything not confidently matched
becomes ``Role.OTHER``.
"""

from __future__ import annotations

from enum import Enum

# NOTE: Python >=3.10 target, so ``class Role(str, Enum)`` rather than enum.StrEnum (3.11+).


class Role(str, Enum):
    """Normalized credit role. ``OTHER`` is the conservative fallback."""

    COMPOSER = "composer"
    ARRANGER = "arranger"
    PERFORMER = "performer"
    VOCALIST = "vocalist"
    LYRICIST = "lyricist"
    PRODUCER = "producer"
    ENGINEER = "engineer"
    MIXING = "mixing"
    MASTERING = "mastering"
    DIRECTOR = "director"
    CONDUCTOR = "conductor"
    ARTWORK = "artwork"
    OTHER = "other"


# Ordered (keyword, role) rules; FIRST substring match wins on the casefolded label.
# Order matters: more specific before generic. Keywords are deliberately specific
# (e.g. "mastering"/"mastered", not bare "master" which also matches "concertmaster";
# "recording", not bare "record" which also matches "record label"). Artwork rules
# precede "direct" so "art direction" is not captured by the DIRECTOR rule; the
# producer rule precedes recording so "recording producer" is a producer credit.
_RULES: tuple[tuple[str, Role], ...] = (
    ("compos", Role.COMPOSER),
    ("orchestrat", Role.ARRANGER),
    ("arrang", Role.ARRANGER),
    ("lyric", Role.LYRICIST),
    ("words", Role.LYRICIST),
    ("written by", Role.LYRICIST),
    ("mastering", Role.MASTERING),
    ("mastered", Role.MASTERING),
    ("mixing", Role.MIXING),
    ("mixed", Role.MIXING),
    ("produc", Role.PRODUCER),
    ("recording", Role.ENGINEER),
    ("recorded", Role.ENGINEER),
    ("engineer", Role.ENGINEER),
    ("pro tools", Role.ENGINEER),
    ("conduct", Role.CONDUCTOR),
    ("illustrat", Role.ARTWORK),
    ("jacket", Role.ARTWORK),
    ("art direction", Role.ARTWORK),
    ("artwork", Role.ARTWORK),
    ("direct", Role.DIRECTOR),
    ("vocal", Role.VOCALIST),
    ("chorus", Role.VOCALIST),
    # instruments -> performer (the specific instrument stays in role_raw)
    ("guitar", Role.PERFORMER),
    ("bass", Role.PERFORMER),
    ("violin", Role.PERFORMER),
    ("viola", Role.PERFORMER),
    ("cello", Role.PERFORMER),
    ("piano", Role.PERFORMER),
    ("keyboard", Role.PERFORMER),
    ("drum", Role.PERFORMER),
    ("percussion", Role.PERFORMER),
    ("flute", Role.PERFORMER),
    ("shakuhachi", Role.PERFORMER),
    ("shinobue", Role.PERFORMER),
    ("bouzouki", Role.PERFORMER),
    ("synthesizer", Role.PERFORMER),
    ("perform", Role.PERFORMER),
)


def normalize_role(raw: str) -> Role:
    """Map a freeform vgmdb role label to a :class:`Role` (conservative; unknown -> OTHER)."""
    label = raw.casefold()
    for keyword, role in _RULES:
        if keyword in label:
            return role
    return Role.OTHER
