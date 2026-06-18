"""Typed pydantic v2 data models for vgmdb-client."""

from vgmdb_client.models.album import Album, Credit, Disc, Track
from vgmdb_client.models.artist import Artist
from vgmdb_client.models.common import ArtistRef, EventRef, LocalizedText, OrgRef, PartialDate, ProductRef
from vgmdb_client.models.event import Event
from vgmdb_client.models.organization import Organization
from vgmdb_client.models.product import Product
from vgmdb_client.models.roles import Role, normalize_role
from vgmdb_client.models.search import AlbumSearchResult, SearchResults

__all__ = [
    "Album",
    "AlbumSearchResult",
    "Artist",
    "ArtistRef",
    "Credit",
    "Disc",
    "Event",
    "EventRef",
    "LocalizedText",
    "OrgRef",
    "Organization",
    "PartialDate",
    "Product",
    "ProductRef",
    "Role",
    "SearchResults",
    "Track",
    "normalize_role",
]
