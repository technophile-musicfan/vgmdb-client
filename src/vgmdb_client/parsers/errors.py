"""Parser-layer errors."""

from __future__ import annotations

from vgmdb_client.errors import VgmdbClientError


class ParseError(VgmdbClientError):
    """Raised when HTML is not a recognizable album/search page."""

    def __init__(self, message: str = "Could not parse the page.") -> None:
        super().__init__(message)


class NotAnAlbumPageError(ParseError):
    """Raised when the HTML lacks the essential anchors of an album page."""

    def __init__(self) -> None:
        super().__init__("Not a vgmdb album page (missing album id or title).")


class NotASearchPageError(ParseError):
    """Raised when the HTML lacks the essential anchors of a search-results page."""

    def __init__(self) -> None:
        super().__init__("Not a vgmdb search-results page (missing results container).")


class NotAnArtistPageError(ParseError):
    """Raised when the HTML lacks the essential anchors of an artist page."""

    def __init__(self) -> None:
        super().__init__("Not a vgmdb artist page (missing artist id or name).")


class NotAProductPageError(ParseError):
    """Raised when the HTML lacks the essential anchors of a product page."""

    def __init__(self) -> None:
        super().__init__("Not a vgmdb product page (missing product id or name).")


class NotAnOrganizationPageError(ParseError):
    """Raised when the HTML lacks the essential anchors of an organization page."""

    def __init__(self) -> None:
        super().__init__("Not a vgmdb organization page (missing organization id or name).")


class NotAnEventPageError(ParseError):
    """Raised when the HTML lacks the essential anchors of an event page."""

    def __init__(self) -> None:
        super().__init__("Not a vgmdb event page (missing event id or name).")
