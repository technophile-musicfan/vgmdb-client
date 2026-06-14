"""Transport-layer error hierarchy."""

from __future__ import annotations

from vgmdb_client.errors import VgmdbClientError


class TransportError(VgmdbClientError):
    """Base class for all transport-layer failures."""

    def __init__(self, message: str = "A transport error occurred.") -> None:
        super().__init__(message)


class CloudflareChallengeError(TransportError):
    """Raised when vgmdb returns a Cloudflare challenge.

    This is not retried: a missing or stale ``cf_clearance`` token will not
    resolve by retrying. Supply or refresh the token and try again.
    """

    def __init__(
        self,
        message: str = "Cloudflare challenge detected; supply or refresh the cf_clearance token.",
    ) -> None:
        super().__init__(message)


class NotFoundError(TransportError):
    """Raised for an application-level 404 (no such resource)."""

    def __init__(self, message: str = "The requested vgmdb resource was not found (404).") -> None:
        super().__init__(message)


class RateLimitedError(TransportError):
    """Raised for a 429 response.

    Exposes ``retry_after`` (seconds) when the server provided a
    ``Retry-After`` header. The transport does not auto-retry rate limits.
    """

    def __init__(
        self,
        message: str = "vgmdb rate-limited the request (429).",
        *,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class TransientTransportError(TransportError):
    """Raised for retryable failures (connection errors, timeouts, 5xx).

    Propagates only after retries are exhausted.
    """

    def __init__(self, message: str = "A transient transport error occurred.") -> None:
        super().__init__(message)
