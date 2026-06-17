"""Asynchronous vgmdb client."""

from __future__ import annotations

from types import TracebackType

from vgmdb_client.client import _core
from vgmdb_client.models import Album, Artist, Organization, Product, SearchResults
from vgmdb_client.parsers import parse_album, parse_artist, parse_organization, parse_product, parse_search
from vgmdb_client.transport import AsyncTransport, TransportConfig

_ONE_SOURCE = "Provide exactly one of `config` or `transport`."


class AsyncClient:
    """Asynchronous vgmdb client. Shares path logic and parsers with :class:`Client`.

    Construct with a :class:`TransportConfig` (an :class:`AsyncTransport` is created internally) or
    inject a ready async transport. Exactly one of ``config``/``transport`` is required. Usable as an
    async context manager that closes the transport on exit.
    """

    def __init__(self, config: TransportConfig | None = None, *, transport: AsyncTransport | None = None) -> None:
        if config is not None and transport is not None:
            raise ValueError(_ONE_SOURCE)
        if transport is not None:
            self._transport = transport
        elif config is not None:
            self._transport = AsyncTransport(config)
        else:
            raise ValueError(_ONE_SOURCE)

    async def get_album(self, album_id: int) -> Album:
        """Fetch and parse an album page."""
        return parse_album(await self._transport.get(_core.album_path(album_id)))

    async def search(self, query: str) -> SearchResults:
        """Fetch and parse a search-results page."""
        return parse_search(await self._transport.get(_core.search_path(query)))

    async def get_artist(self, artist_id: int) -> Artist:
        """Fetch and parse an artist page."""
        return parse_artist(await self._transport.get(_core.artist_path(artist_id)))

    async def get_product(self, product_id: int) -> Product:
        """Fetch and parse a product page."""
        return parse_product(await self._transport.get(_core.product_path(product_id)))

    async def get_organization(self, org_id: int) -> Organization:
        """Fetch and parse an organization page."""
        return parse_organization(await self._transport.get(_core.organization_path(org_id)))

    async def aclose(self) -> None:
        """Close the underlying transport."""
        await self._transport.aclose()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()
