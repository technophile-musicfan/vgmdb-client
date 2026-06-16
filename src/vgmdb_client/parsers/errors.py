"""Parser-layer errors."""

from __future__ import annotations

from vgmdb_client.errors import VgmdbClientError


class ParseError(VgmdbClientError):
    """Raised when HTML is not a recognizable album/search page."""

    def __init__(self, message: str = "Could not parse the page.") -> None:
        super().__init__(message)
