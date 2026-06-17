"""The canonical comparison record: the compared field set and the scoring normalizer.

A *canonical record* is a flat ``dict[str, str | None]`` mapping a field path to its value, already
reduced to a string by the adapters (``LocalizedText`` -> default language, ``PartialDate`` -> ISO).
The :func:`normalize` function is then applied only at scoring time so that values that differ only
in whitespace or case still compare equal.
"""

from __future__ import annotations

# Album-level field paths every source is reduced to. Per-track titles are added dynamically as
# ``disc{d}.track{t}.title`` (1-based disc/track ordinals, positionally aligned across sources).
ALBUM_FIELDS: tuple[str, ...] = ("title", "catalog", "release_date", "classification")


def track_field(disc_number: int, track_number: int) -> str:
    """Return the canonical field path for a track title (1-based ordinals)."""
    return f"disc{disc_number}.track{track_number}.title"


def normalize(value: str | None) -> str | None:
    """Collapse whitespace and casefold for fair comparison; empty/blank becomes ``None``."""
    if value is None:
        return None
    collapsed = " ".join(value.split())
    return collapsed.casefold() or None
