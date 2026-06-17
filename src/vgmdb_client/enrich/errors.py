"""Enrichment-layer errors."""

from __future__ import annotations

from vgmdb_client.errors import VgmdbClientError


class EnrichmentError(VgmdbClientError):
    """Raised when a configured enrichment backend fails to produce a valid result."""

    def __init__(self, message: str = "Enrichment failed.") -> None:
        super().__init__(message)
