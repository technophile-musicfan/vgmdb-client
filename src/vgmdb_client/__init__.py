"""vgmdb-client: a typed, direct-to-vgmdb.net Python client."""

from vgmdb_client.client import AsyncClient, Client
from vgmdb_client.errors import VgmdbClientError
from vgmdb_client.models import (
    Album,
    AlbumSearchResult,
    Artist,
    ArtistRef,
    Credit,
    Disc,
    LocalizedText,
    Organization,
    OrgRef,
    PartialDate,
    Product,
    ProductRef,
    Role,
    SearchResults,
    Track,
    normalize_role,
)
from vgmdb_client.parsers import ParseError
from vgmdb_client.transport import (
    CloudflareChallengeError,
    NotFoundError,
    RateLimitedError,
    TransientTransportError,
    TransportConfig,
    TransportError,
)

__all__ = [
    "Album",
    "AlbumSearchResult",
    "Artist",
    "ArtistRef",
    "AsyncClient",
    "Client",
    "CloudflareChallengeError",
    "Credit",
    "Disc",
    "LocalizedText",
    "NotFoundError",
    "OrgRef",
    "Organization",
    "ParseError",
    "PartialDate",
    "Product",
    "ProductRef",
    "RateLimitedError",
    "Role",
    "SearchResults",
    "Track",
    "TransientTransportError",
    "TransportConfig",
    "TransportError",
    "VgmdbClientError",
    "normalize_role",
]
