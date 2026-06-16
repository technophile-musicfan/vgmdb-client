"""Search results page parser (clean-room, owned selectors)."""

from __future__ import annotations

from vgmdb_client.models import SearchResults


def parse_search(html: str) -> SearchResults:
    raise NotImplementedError
