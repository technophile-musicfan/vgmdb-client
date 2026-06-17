"""Clean-room HTML -> M1 model parsers for vgmdb pages."""

from vgmdb_client.parsers.album import parse_album
from vgmdb_client.parsers.artist import parse_artist
from vgmdb_client.parsers.errors import (
    NotAnArtistPageError,
    NotAnOrganizationPageError,
    NotAProductPageError,
    ParseError,
)
from vgmdb_client.parsers.organization import parse_organization
from vgmdb_client.parsers.product import parse_product
from vgmdb_client.parsers.search import parse_search

__all__ = [
    "NotAProductPageError",
    "NotAnArtistPageError",
    "NotAnOrganizationPageError",
    "ParseError",
    "parse_album",
    "parse_artist",
    "parse_organization",
    "parse_product",
    "parse_search",
]
