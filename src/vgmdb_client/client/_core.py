"""Shared request-path builders for the clients (pure, no I/O)."""

from __future__ import annotations

from urllib.parse import quote_plus


def album_path(album_id: int) -> str:
    """The request path for an album page."""
    return f"/album/{album_id}"


def search_path(query: str) -> str:
    """The request path for a search, with the query URL-encoded."""
    return f"/search?q={quote_plus(query)}"
