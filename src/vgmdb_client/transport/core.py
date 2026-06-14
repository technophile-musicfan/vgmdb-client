"""Sans-I/O core for the transport layer.

Pure functions shared by the sync and async clients: response classification,
Cloudflare-challenge detection, retry-after parsing, the tenacity retry policy,
and throttle wait-time calculation. Nothing here performs I/O.
"""

from __future__ import annotations

from collections.abc import Mapping

from tenacity import (
    AsyncRetrying,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from vgmdb_client.transport.config import TransportConfig
from vgmdb_client.transport.errors import (
    CloudflareChallengeError,
    NotFoundError,
    RateLimitedError,
    TransientTransportError,
    TransportError,
)

CF_COOKIE_NAME = "cf_clearance"

_CF_BODY_SIGNATURES = (
    "just a moment",
    "cf-chl",
    "challenge-platform",
    "checking your browser",
)


def build_headers(user_agent: str) -> dict[str, str]:
    """Build the default request headers from the configured User-Agent."""
    return {"User-Agent": user_agent}


def build_cookies(cf_clearance: str | None) -> dict[str, str]:
    """Build the request cookies, including ``cf_clearance`` when present."""
    if cf_clearance:
        return {CF_COOKIE_NAME: cf_clearance}
    return {}


def _lower_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {key.lower(): value for key, value in headers.items()}


def is_cloudflare_challenge(status: int, headers: Mapping[str, str], text: str) -> bool:
    """Return True if the response looks like a Cloudflare challenge."""
    if status not in (403, 503):
        return False
    lowered = _lower_headers(headers)
    if lowered.get("cf-mitigated", "").lower() == "challenge":
        return True
    body = (text or "").lower()
    has_signature = any(signature in body for signature in _CF_BODY_SIGNATURES)
    has_cf_headers = lowered.get("server", "").lower() == "cloudflare" or "cf-ray" in lowered
    return has_signature and has_cf_headers


def parse_retry_after(headers: Mapping[str, str]) -> float | None:
    """Parse the ``Retry-After`` header as seconds, or None if absent/non-numeric."""
    raw = _lower_headers(headers).get("retry-after")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def classify_response(status: int, headers: Mapping[str, str], text: str) -> None:
    """Inspect a response and raise the appropriate transport error.

    Returns ``None`` for a successful (2xx) response. Detection order: 2xx ok →
    404 → Cloudflare challenge → 429 → other 5xx (transient) → other (generic).
    """
    if 200 <= status < 300:
        return None
    if status == 404:
        raise NotFoundError
    if is_cloudflare_challenge(status, headers, text):
        raise CloudflareChallengeError
    if status == 429:
        raise RateLimitedError(retry_after=parse_retry_after(headers))
    if status >= 500:
        raise TransientTransportError
    raise TransportError


def is_retryable_exception(exc: BaseException) -> bool:
    """Return True only for transient failures that should be retried."""
    return isinstance(exc, TransientTransportError)


def throttle_wait(last: float | None, now: float, min_interval: float) -> float:
    """Seconds to wait before the next request to honor ``min_interval``."""
    if min_interval <= 0 or last is None:
        return 0.0
    remaining = min_interval - (now - last)
    return remaining if remaining > 0 else 0.0


def _retry_kwargs(config: TransportConfig) -> dict[str, object]:
    return {
        "retry": retry_if_exception(is_retryable_exception),
        "stop": stop_after_attempt(config.max_retries + 1),
        "wait": wait_random_exponential(multiplier=config.backoff_base, max=config.backoff_max),
        "reraise": True,
    }


def build_retrying(config: TransportConfig) -> Retrying:
    """Build a synchronous tenacity controller from config."""
    return Retrying(**_retry_kwargs(config))  # type: ignore[arg-type]


def build_async_retrying(config: TransportConfig) -> AsyncRetrying:
    """Build an asynchronous tenacity controller from config."""
    return AsyncRetrying(**_retry_kwargs(config))  # type: ignore[arg-type]
