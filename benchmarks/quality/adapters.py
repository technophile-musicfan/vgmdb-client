"""Adapt each source (our Album, the golden Album, a hufman JSON response) to a canonical record."""

from __future__ import annotations

from typing import Any

from benchmarks.quality.fields import track_field
from vgmdb_client.models import Album

CanonicalRecord = dict[str, str | None]

# Languages tried, in order, when reducing a hufman name mapping to a single string.
_HUFMAN_NAME_PREFERENCE = ("English", "Romaji", "en", "ja-latn", "ja")


def from_album(album: Album) -> CanonicalRecord:
    """Reduce our parsed (or golden) :class:`Album` to a canonical record."""
    record: CanonicalRecord = {
        "title": album.titles.default,
        "catalog": album.catalog,
        "release_date": str(album.release_date) if album.release_date is not None else None,
        "classification": album.classification,
    }
    for disc_number, disc in enumerate(album.discs, start=1):
        for track_number, track in enumerate(disc.tracks, start=1):
            record[track_field(disc_number, track_number)] = track.titles.default
    return record


def from_golden(album: Album) -> CanonicalRecord:
    """Reduce the golden :class:`Album` to a canonical record (same shape as :func:`from_album`)."""
    return from_album(album)


def from_hufman(data: dict[str, Any]) -> CanonicalRecord:
    """Reduce a hufman ``/album`` JSON response to a canonical record.

    Tolerant by design: any field absent from the response maps to ``None`` rather than raising, so
    hufman API differences degrade to "missing" instead of crashing the run.
    """
    record: CanonicalRecord = {
        "title": _name_text(data.get("name", data.get("names"))),
        "catalog": _as_text(data.get("catalog")),
        "release_date": _as_text(data.get("release_date")),
        "classification": _as_text(data.get("classification")),
    }
    discs = data.get("discs")
    if isinstance(discs, list):
        for disc_number, disc in enumerate(discs, start=1):
            tracks = disc.get("tracks") if isinstance(disc, dict) else None
            if not isinstance(tracks, list):
                continue
            for track_number, track in enumerate(tracks, start=1):
                names = track.get("names") if isinstance(track, dict) else track
                record[track_field(disc_number, track_number)] = _name_text(names)
    return record


def _as_text(value: Any) -> str | None:
    """Return a non-empty string value, else ``None``."""
    if isinstance(value, str) and value.strip():
        return value
    return None


def _name_text(names: Any) -> str | None:
    """Reduce a hufman name (a string, or a language->text mapping) to a single string."""
    if isinstance(names, str):
        return _as_text(names)
    if isinstance(names, dict):
        for language in _HUFMAN_NAME_PREFERENCE:
            text = _as_text(names.get(language))
            if text is not None:
                return text
        for value in names.values():
            text = _as_text(value)
            if text is not None:
                return text
    return None
