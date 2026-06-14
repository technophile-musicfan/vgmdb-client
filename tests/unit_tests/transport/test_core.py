"""Tests for the sans-I/O transport core."""

import pytest

from vgmdb_client.transport.config import TransportConfig
from vgmdb_client.transport.core import (
    CF_COOKIE_NAME,
    build_cookies,
    build_headers,
    build_retrying,
    classify_response,
    is_retryable_exception,
    parse_retry_after,
    throttle_wait,
)
from vgmdb_client.transport.errors import (
    CloudflareChallengeError,
    NotFoundError,
    RateLimitedError,
    TransientTransportError,
    TransportError,
)

CF_HEADERS = {"server": "cloudflare", "cf-ray": "abc123"}


# --- classify_response truth table ---------------------------------------


def test_2xx_returns_none() -> None:
    assert classify_response(200, {}, "<html>ok</html>") is None
    assert classify_response(204, {}, "") is None


def test_404_raises_not_found() -> None:
    with pytest.raises(NotFoundError):
        classify_response(404, {}, "not found")


def test_403_with_cf_mitigated_header_is_challenge() -> None:
    with pytest.raises(CloudflareChallengeError):
        classify_response(403, {"cf-mitigated": "challenge"}, "")


def test_503_with_body_signature_and_cf_headers_is_challenge() -> None:
    with pytest.raises(CloudflareChallengeError):
        classify_response(503, CF_HEADERS, "<title>Just a moment...</title>")


def test_403_without_cf_markers_is_generic_transport_error() -> None:
    with pytest.raises(TransportError) as excinfo:
        classify_response(403, {}, "forbidden")
    assert excinfo.type is TransportError


def test_503_without_cf_markers_is_transient() -> None:
    with pytest.raises(TransientTransportError):
        classify_response(503, {}, "service unavailable")


def test_429_raises_rate_limited_with_retry_after() -> None:
    with pytest.raises(RateLimitedError) as excinfo:
        classify_response(429, {"retry-after": "30"}, "slow down")
    assert excinfo.value.retry_after == 30.0


def test_500_is_transient() -> None:
    with pytest.raises(TransientTransportError):
        classify_response(500, {}, "boom")


# --- parse_retry_after ----------------------------------------------------


def test_parse_retry_after_numeric() -> None:
    assert parse_retry_after({"retry-after": "12"}) == 12.0


def test_parse_retry_after_missing() -> None:
    assert parse_retry_after({}) is None


def test_parse_retry_after_non_numeric() -> None:
    assert parse_retry_after({"retry-after": "Wed, 21 Oct 2026 07:28:00 GMT"}) is None


def test_headers_are_case_insensitive() -> None:
    with pytest.raises(CloudflareChallengeError):
        classify_response(403, {"CF-Mitigated": "challenge"}, "")


# --- is_retryable_exception ----------------------------------------------


def test_only_transient_is_retryable() -> None:
    assert is_retryable_exception(TransientTransportError("x")) is True
    assert is_retryable_exception(NotFoundError("x")) is False
    assert is_retryable_exception(CloudflareChallengeError("x")) is False
    assert is_retryable_exception(RateLimitedError("x")) is False
    assert is_retryable_exception(ValueError("x")) is False


# --- throttle_wait --------------------------------------------------------


def test_throttle_wait_no_previous_request() -> None:
    assert throttle_wait(None, now=100.0, min_interval=1.0) == 0.0


def test_throttle_wait_interval_elapsed() -> None:
    assert throttle_wait(100.0, now=102.0, min_interval=1.0) == 0.0


def test_throttle_wait_remaining() -> None:
    assert throttle_wait(100.0, now=100.4, min_interval=1.0) == pytest.approx(0.6)


def test_throttle_wait_disabled() -> None:
    assert throttle_wait(100.0, now=100.0, min_interval=0.0) == 0.0


# --- header / cookie assembly --------------------------------------------


def test_build_headers_sets_user_agent() -> None:
    assert build_headers("UA/1.0") == {"User-Agent": "UA/1.0"}


def test_build_cookies_includes_cf_clearance_when_set() -> None:
    assert build_cookies("token") == {CF_COOKIE_NAME: "token"}


def test_build_cookies_empty_when_token_absent() -> None:
    assert build_cookies(None) == {}


# --- build_retrying behavior ---------------------------------------------


def _fast_config(**kwargs: object) -> TransportConfig:
    return TransportConfig(user_agent="UA/1.0", backoff_base=0.001, backoff_max=0.01, **kwargs)  # type: ignore[arg-type]


def test_retrying_retries_transient_then_succeeds() -> None:
    retrying = build_retrying(_fast_config(max_retries=3))
    attempts = {"n": 0}

    def flaky() -> str:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise TransientTransportError("temp")
        return "ok"

    assert retrying(flaky) == "ok"
    assert attempts["n"] == 3


def test_retrying_reraises_after_exhaustion() -> None:
    retrying = build_retrying(_fast_config(max_retries=2))
    attempts = {"n": 0}

    def always_fail() -> str:
        attempts["n"] += 1
        raise TransientTransportError("temp")

    with pytest.raises(TransientTransportError):
        retrying(always_fail)
    assert attempts["n"] == 3  # max_retries + 1


def test_retrying_does_not_retry_non_transient() -> None:
    retrying = build_retrying(_fast_config(max_retries=3))
    attempts = {"n": 0}

    def fail_not_found() -> str:
        attempts["n"] += 1
        raise NotFoundError("nope")

    with pytest.raises(NotFoundError):
        retrying(fail_not_found)
    assert attempts["n"] == 1
