"""vgmdb-client: a typed, direct-to-vgmdb.net Python client."""

from vgmdb_client.client import AsyncClient, Client
from vgmdb_client.errors import VgmdbClientError
from vgmdb_client.models import (
    Album,
    AlbumSearchResult,
    ArtistRef,
    Credit,
    Disc,
    LocalizedText,
    PartialDate,
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
    "ArtistRef",
    "AsyncClient",
    "Client",
    "CloudflareChallengeError",
    "Credit",
    "Disc",
    "LocalizedText",
    "NotFoundError",
    "ParseError",
    "PartialDate",
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
