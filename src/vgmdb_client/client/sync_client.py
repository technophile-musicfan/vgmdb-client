"""Synchronous vgmdb client."""

from __future__ import annotations

from types import TracebackType
from typing import Any

from vgmdb_client.auth import Credentials
from vgmdb_client.client import _core
from vgmdb_client.models import Album, Artist, Organization, Product, SearchResults
from vgmdb_client.parsers import parse_album, parse_artist, parse_organization, parse_product, parse_search
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

    @classmethod
    def from_credentials(cls, credentials: Credentials, **config_overrides: Any) -> Client:
        """Build a client from a :class:`Credentials` pair (initial fill).

        Extra keyword arguments are forwarded to :meth:`Credentials.to_config` as
        :class:`TransportConfig` overrides (e.g. ``timeout``, ``min_interval``, ``proxy``).
        """
        return cls(config=credentials.to_config(**config_overrides))

    def set_credentials(self, credentials: Credentials) -> None:
        """Apply a fresh :class:`Credentials` pair to the live client (renewal).

        Use after a :class:`~vgmdb_client.transport.errors.CloudflareChallengeError`: re-solve in the
        browser, copy a fresh cURL, and swap the pair in without rebuilding the client.
        """
        self._transport.set_cf_clearance(credentials.cf_clearance)
        self._transport.set_user_agent(credentials.user_agent)

    def get_album(self, album_id: int) -> Album:
        """Fetch and parse an album page."""
        return parse_album(self._transport.get(_core.album_path(album_id)))

    def search(self, query: str) -> SearchResults:
        """Fetch and parse a search-results page."""
        return parse_search(self._transport.get(_core.search_path(query)))

    def get_artist(self, artist_id: int) -> Artist:
        """Fetch and parse an artist page."""
        return parse_artist(self._transport.get(_core.artist_path(artist_id)))

    def get_product(self, product_id: int) -> Product:
        """Fetch and parse a product page."""
        return parse_product(self._transport.get(_core.product_path(product_id)))

    def get_organization(self, org_id: int) -> Organization:
        """Fetch and parse an organization page."""
        return parse_organization(self._transport.get(_core.organization_path(org_id)))

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
