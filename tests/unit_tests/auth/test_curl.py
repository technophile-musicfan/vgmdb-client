"""Tests for the clean-room cURL parser."""

from __future__ import annotations

import pytest

from vgmdb_client.auth.curl import parse_curl
from vgmdb_client.auth.errors import CurlParseError

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120"

CHROME_CURL = (
    "curl 'https://vgmdb.net/album/4' \\\n"
    "  -H 'authority: vgmdb.net' \\\n"
    f"  -H 'user-agent: {_UA}' \\\n"
    "  -H 'cookie: cf_clearance=abc123.def456; PHPSESSID=zzz' \\\n"
    "  --compressed"
)


def test_extracts_both_from_chrome_paste() -> None:
    cf_clearance, user_agent = parse_curl(CHROME_CURL)
    assert cf_clearance == "abc123.def456"
    assert user_agent == _UA


def test_selects_cf_clearance_from_multi_cookie_header() -> None:
    curl = (
        "curl 'https://vgmdb.net/album/4' "
        "-H 'Cookie: foo=1; cf_clearance=TOK; bar=2' "
        "-H 'User-Agent: UA/1.0'"
    )
    cf_clearance, _ = parse_curl(curl)
    assert cf_clearance == "TOK"


def test_reads_short_flag_forms() -> None:
    curl = "curl https://vgmdb.net/album/4 -b 'cf_clearance=TOK; other=x' -A 'UA/2.0'"
    cf_clearance, user_agent = parse_curl(curl)
    assert cf_clearance == "TOK"
    assert user_agent == "UA/2.0"


def test_header_names_are_case_insensitive() -> None:
    curl = "curl https://vgmdb.net/album/4 -H 'COOKIE: cf_clearance=TOK' -H 'USER-AGENT: UA/3.0'"
    cf_clearance, user_agent = parse_curl(curl)
    assert cf_clearance == "TOK"
    assert user_agent == "UA/3.0"


def test_last_occurrence_wins() -> None:
    curl = (
        "curl https://vgmdb.net/album/4 "
        "-H 'User-Agent: OLD' -H 'User-Agent: NEW' "
        "-b 'cf_clearance=OLD' -b 'cf_clearance=NEW'"
    )
    cf_clearance, user_agent = parse_curl(curl)
    assert cf_clearance == "NEW"
    assert user_agent == "NEW"


def test_missing_cf_clearance_raises() -> None:
    curl = "curl https://vgmdb.net/album/4 -H 'Cookie: PHPSESSID=zzz' -H 'User-Agent: UA/1.0'"
    with pytest.raises(CurlParseError, match="cf_clearance"):
        parse_curl(curl)


def test_missing_user_agent_raises() -> None:
    curl = "curl https://vgmdb.net/album/4 -H 'Cookie: cf_clearance=TOK'"
    with pytest.raises(CurlParseError, match="User-Agent"):
        parse_curl(curl)


def test_unparseable_input_raises() -> None:
    with pytest.raises(CurlParseError):
        parse_curl("curl 'unbalanced quote")
