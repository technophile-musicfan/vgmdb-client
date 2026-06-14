"""Tests for the library-wide base error."""

import pytest

from vgmdb_client.errors import VgmdbClientError


def test_vgmdb_client_error_is_exception() -> None:
    assert issubclass(VgmdbClientError, Exception)


def test_vgmdb_client_error_can_be_raised_and_caught() -> None:
    with pytest.raises(VgmdbClientError, match="boom"):
        raise VgmdbClientError("boom")
