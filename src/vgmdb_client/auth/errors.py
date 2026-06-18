"""Auth-helper error hierarchy."""

from __future__ import annotations

from vgmdb_client.errors import VgmdbClientError

_DEFAULT = (
    "Could not extract a cf_clearance cookie and User-Agent from the cURL command. In your browser "
    "devtools, copy a request to vgmdb.net as cURL (bash) including its Cookie and User-Agent headers."
)


class CurlParseError(VgmdbClientError):
    """Raised when a pasted cURL command lacks a ``cf_clearance`` cookie or a ``User-Agent``,
    or cannot be tokenized as a shell command."""

    def __init__(self, message: str = _DEFAULT) -> None:
        super().__init__(message)
