"""Tests for TransportConfig."""

import pytest
from pydantic import ValidationError

from vgmdb_client.transport.config import TransportConfig


def test_defaults_applied_with_only_user_agent() -> None:
    config = TransportConfig(user_agent="UA/1.0")

    assert config.base_url == "https://vgmdb.net"
    assert config.user_agent == "UA/1.0"
    assert config.cf_clearance is None
    assert config.timeout == 10.0
    assert config.max_retries == 3
    assert config.backoff_base == 0.5
    assert config.backoff_max == 8.0
    assert config.min_interval == 1.0
    assert config.proxy is None


def test_user_agent_is_required() -> None:
    with pytest.raises(ValidationError):
        TransportConfig()  # type: ignore[call-arg]


def test_fields_can_be_overridden() -> None:
    config = TransportConfig(
        base_url="https://example.test",
        user_agent="UA/2.0",
        cf_clearance="token",
        timeout=5.0,
        max_retries=1,
        backoff_base=0.1,
        backoff_max=2.0,
        min_interval=0.0,
        proxy="http://proxy.test:8080",
    )

    assert config.base_url == "https://example.test"
    assert config.cf_clearance == "token"
    assert config.timeout == 5.0
    assert config.max_retries == 1
    assert config.min_interval == 0.0
    assert config.proxy == "http://proxy.test:8080"


def test_negative_min_interval_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TransportConfig(user_agent="UA/1.0", min_interval=-1.0)


def test_non_positive_timeout_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TransportConfig(user_agent="UA/1.0", timeout=0.0)
