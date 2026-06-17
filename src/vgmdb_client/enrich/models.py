"""Enrichment overlay models — structured fields layered on an Album without changing M1."""

from __future__ import annotations

from pydantic import Field

from vgmdb_client.models import Credit
from vgmdb_client.models.common import VgmdbModel


class AlbumEnrichment(VgmdbModel):
    """Per-track credits extracted from an album's freeform notes, keyed by track number.

    A separate overlay: it does not modify the M1 ``Album``/``Track`` models. ``is_empty`` is true
    when no track carries any credit (e.g. when no backend was configured).
    """

    album_id: int
    track_credits: dict[int, list[Credit]] = Field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not any(self.track_credits.values())
