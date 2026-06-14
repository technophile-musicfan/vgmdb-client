"""Tests for the transport error hierarchy."""

import pytest

from vgmdb_client.errors import VgmdbClientError
from vgmdb_client.transport.errors import (
    CloudflareChallengeError,
    NotFoundError,
    RateLimitedError,
    TransientTransportError,
    TransportError,
)

SPECIFIC_ERRORS = [
    CloudflareChallengeError,
    NotFoundError,
    RateLimitedError,
    TransientTransportError,
]


def test_transport_error_derives_from_library_base() -> None:
    assert issubclass(TransportError, VgmdbClientError)


@pytest.mark.parametrize("error_cls", SPECIFIC_ERRORS)
def test_specific_errors_share_transport_and_library_base(error_cls: type[TransportError]) -> None:
    assert issubclass(error_cls, TransportError)
    assert issubclass(error_cls, VgmdbClientError)


@pytest.mark.parametrize("error_cls", SPECIFIC_ERRORS)
def test_specific_errors_catchable_as_bases(error_cls: type[TransportError]) -> None:
    with pytest.raises(TransportError):
        raise error_cls("boom")
    with pytest.raises(VgmdbClientError):
        raise error_cls("boom")


def test_rate_limited_error_exposes_retry_after() -> None:
    error = RateLimitedError("slow down", retry_after=12.0)
    assert error.retry_after == 12.0


def test_rate_limited_error_retry_after_defaults_to_none() -> None:
    error = RateLimitedError("slow down")
    assert error.retry_after is None
