"""HTTP transport layer for vgmdb-client.

Authenticated, Cloudflare-aware fetching of vgmdb pages with sync and async
clients over a shared sans-I/O core.
"""

from vgmdb_client.transport.async_client import AsyncTransport
from vgmdb_client.transport.config import TransportConfig
from vgmdb_client.transport.errors import (
    CloudflareChallengeError,
    NotFoundError,
    RateLimitedError,
    TransientTransportError,
    TransportError,
)
from vgmdb_client.transport.sync_client import SyncTransport

__all__ = [
    "AsyncTransport",
    "CloudflareChallengeError",
    "NotFoundError",
    "RateLimitedError",
    "SyncTransport",
    "TransientTransportError",
    "TransportConfig",
    "TransportError",
]
