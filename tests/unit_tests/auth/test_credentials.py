"""Tests for the Credentials value object."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from vgmdb_client.auth import Credentials
from vgmdb_client.transport import TransportConfig

_UA = "Mozilla/5.0 Chrome/120"
CURL = f"curl https://vgmdb.net/album/4 -H 'Cookie: cf_clearance=TOK' -H 'User-Agent: {_UA}'"


def test_from_curl_round_trip() -> None:
    creds = Credentials.from_curl(CURL)
    assert creds.cf_clearance == "TOK"
    assert creds.user_agent == _UA


def test_to_config_carries_pair() -> None:
    config = Credentials(cf_clearance="TOK", user_agent=_UA).to_config()
    assert isinstance(config, TransportConfig)
    assert config.cf_clearance == "TOK"
    assert config.user_agent == _UA


def test_to_config_forwards_overrides() -> None:
    config = Credentials(cf_clearance="TOK", user_agent=_UA).to_config(min_interval=0, timeout=5.0)
    assert config.min_interval == 0
    assert config.timeout == 5.0
    assert config.cf_clearance == "TOK"


@pytest.mark.parametrize(("cf_clearance", "user_agent"), [("", _UA), ("TOK", ""), ("TOK", "   ")])
def test_empty_field_rejected(cf_clearance: str, user_agent: str) -> None:
    with pytest.raises(ValidationError):
        Credentials(cf_clearance=cf_clearance, user_agent=user_agent)


def test_is_immutable() -> None:
    creds = Credentials(cf_clearance="TOK", user_agent=_UA)
    with pytest.raises(ValidationError):
        creds.cf_clearance = "OTHER"  # type: ignore[misc]


def test_auth_public_surface() -> None:
    import vgmdb_client.auth as auth
    from vgmdb_client.auth import Credentials as ExportedCredentials
    from vgmdb_client.auth import CurlParseError as ExportedError

    assert set(auth.__all__) == {"Credentials", "CurlParseError"}
    assert ExportedCredentials is auth.Credentials
    assert ExportedError is auth.CurlParseError
