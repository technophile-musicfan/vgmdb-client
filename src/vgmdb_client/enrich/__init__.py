"""Opt-in deep-parse enrichment: structured overlays from freeform vgmdb text."""

from __future__ import annotations

from vgmdb_client.enrich.backend import EnrichmentBackend
from vgmdb_client.enrich.errors import EnrichmentError
from vgmdb_client.enrich.llm import OpenAICompatibleBackend, backend_from_env
from vgmdb_client.enrich.models import AlbumEnrichment
from vgmdb_client.enrich.rules import RuleBasedBackend
from vgmdb_client.models import Album

__all__ = [
    "AlbumEnrichment",
    "EnrichmentBackend",
    "EnrichmentError",
    "OpenAICompatibleBackend",
    "RuleBasedBackend",
    "backend_from_env",
    "enrich_album",
]


def enrich_album(album: Album, backend: EnrichmentBackend | None = None) -> AlbumEnrichment:
    """Enrich an album's per-track credits from its notes via ``backend``.

    With no backend this degrades gracefully to an empty :class:`AlbumEnrichment` (the M3 album is
    fully usable); a configured backend that fails raises :class:`EnrichmentError`.
    """
    if backend is None:
        return AlbumEnrichment(album_id=album.id)
    return backend.enrich(album, album.notes or "")
