"""Transport-layer error hierarchy."""

from __future__ import annotations

from vgmdb_client.errors import VgmdbClientError


class TransportError(VgmdbClientError):
    """Base class for all transport-layer failures."""


class CloudflareChallengeError(TransportError):
    """Raised when vgmdb returns a Cloudflare challenge.

    This is not retried: a missing or stale ``cf_clearance`` token will not
    resolve by retrying. Supply or refresh the token and try again.
    """


class NotFoundError(TransportError):
    """Raised for an application-level 404 (no such resource)."""


class RateLimitedError(TransportError):
    """Raised for a 429 response.

    Exposes ``retry_after`` (seconds) when the server provided a
    ``Retry-After`` header. The transport does not auto-retry rate limits.
    """

    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class TransientTransportError(TransportError):
    """Raised for retryable failures (connection errors, timeouts, 5xx).

    Propagates only after retries are exhausted.
    """
