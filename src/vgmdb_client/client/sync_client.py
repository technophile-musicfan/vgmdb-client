"""Synchronous vgmdb client."""

from __future__ import annotations

from types import TracebackType

from vgmdb_client.client import _core
from vgmdb_client.models import Album, Artist, SearchResults
from vgmdb_client.parsers import parse_album, parse_artist, parse_search
from vgmdb_client.transport import SyncTransport, TransportConfig

_ONE_SOURCE = "Provide exactly one of `config` or `transport`."


class Client:
    """Synchronous vgmdb client: fetch + parse album/search pages into M1 models.

    Construct with a :class:`TransportConfig` (a :class:`SyncTransport` is created internally) or
    inject a ready transport (e.g. a stub in tests). Exactly one of ``config``/``transport`` is
    required. Usable as a context manager that closes the transport on exit.
    """

    def __init__(self, config: TransportConfig | None = None, *, transport: SyncTransport | None = None) -> None:
        if config is not None and transport is not None:
            raise ValueError(_ONE_SOURCE)
        if transport is not None:
            self._transport = transport
        elif config is not None:
            self._transport = SyncTransport(config)
        else:
            raise ValueError(_ONE_SOURCE)

    def get_album(self, album_id: int) -> Album:
        """Fetch and parse an album page."""
        return parse_album(self._transport.get(_core.album_path(album_id)))

    def search(self, query: str) -> SearchResults:
        """Fetch and parse a search-results page."""
        return parse_search(self._transport.get(_core.search_path(query)))

    def get_artist(self, artist_id: int) -> Artist:
        """Fetch and parse an artist page."""
        return parse_artist(self._transport.get(_core.artist_path(artist_id)))

    def close(self) -> None:
        """Close the underlying transport."""
        self._transport.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
