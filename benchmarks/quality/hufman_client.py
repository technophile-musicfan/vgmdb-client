"""Thin HTTP client for a self-hosted hufman/vgmdb (vgmdb.info) service.

hufman runs only as an external Docker service; no hufman code is vendored or imported. The client
returns the album JSON dict, or ``None`` when the service is unreachable or the response is unusable,
so the harness can simply drop the hufman column.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

_DEFAULT_URL = "http://localhost:5000"
_DEFAULT_TIMEOUT = 10.0


def hufman_base_url() -> str:
    """Return the configured hufman base URL (``HUFMAN_URL``, default ``http://localhost:5000``)."""
    return os.environ.get("HUFMAN_URL") or _DEFAULT_URL


def fetch_album(
    album_id: int,
    base_url: str | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> dict[str, Any] | None:
    """GET ``<base>/album/<id>?format=json`` from hufman; return its dict or ``None`` if unavailable."""
    url = (base_url or hufman_base_url()).rstrip("/") + f"/album/{album_id}"
    try:
        response = httpx.get(url, params={"format": "json"}, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError):
        return None
    return data if isinstance(data, dict) else None
