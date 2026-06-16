"""Album page parser (clean-room, owned selectors)."""

from __future__ import annotations

from vgmdb_client.models import Album


def parse_album(html: str) -> Album:
    raise NotImplementedError
