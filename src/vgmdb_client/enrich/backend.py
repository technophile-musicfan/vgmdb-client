"""The pluggable enrichment backend protocol."""

from __future__ import annotations

from typing import Protocol

from vgmdb_client.enrich.models import AlbumEnrichment
from vgmdb_client.models import Album


class EnrichmentBackend(Protocol):
    """A source of enrichment for an album's freeform text.

    Implementations (an LLM endpoint now, an embedded model later) are interchangeable.
    """

    def enrich(self, album: Album, raw_text: str) -> AlbumEnrichment:
        """Return the enrichment for ``album`` derived from its freeform ``raw_text``."""
        ...
