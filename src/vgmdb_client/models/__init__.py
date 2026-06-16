"""Typed pydantic v2 data models for vgmdb-client."""

from vgmdb_client.models.album import Album, Credit, Disc, Track
from vgmdb_client.models.common import ArtistRef, LocalizedText, PartialDate
from vgmdb_client.models.roles import Role, normalize_role
from vgmdb_client.models.search import AlbumSearchResult, SearchResults

__all__ = [
    "Album",
    "AlbumSearchResult",
    "ArtistRef",
    "Credit",
    "Disc",
    "LocalizedText",
    "PartialDate",
    "Role",
    "SearchResults",
    "Track",
    "normalize_role",
]
