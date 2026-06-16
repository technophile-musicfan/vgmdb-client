"""Clean-room HTML -> M1 model parsers for vgmdb pages."""

from vgmdb_client.parsers.album import parse_album
from vgmdb_client.parsers.errors import ParseError
from vgmdb_client.parsers.search import parse_search

__all__ = ["ParseError", "parse_album", "parse_search"]
