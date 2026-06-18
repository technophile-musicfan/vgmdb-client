"""Clean-room parser for a browser "Copy as cURL" command.

Extracts the ``cf_clearance`` cookie and the ``User-Agent`` from a pasted cURL command (the bash
single-quote form Chrome/Firefox emit). Pure and standard-library only — no network, no cURL binary.
"""

from __future__ import annotations

import shlex

from vgmdb_client.auth.errors import CurlParseError

_CF_COOKIE = "cf_clearance"
_NO_CLEARANCE = (
    "No cf_clearance cookie found in the cURL command; copy a request to vgmdb.net that carries the "
    "cf_clearance cookie."
)
_NO_UA = "No User-Agent found in the cURL command; copy the request including its User-Agent header."
_UNPARSEABLE = "Could not tokenize the cURL command; paste the bash 'Copy as cURL' form."


def parse_curl(curl_text: str) -> tuple[str, str]:
    """Return ``(cf_clearance, user_agent)`` parsed from a cURL command.

    Reads the token from a ``-H 'Cookie: ...'`` header or a ``-b``/``--cookie`` value (selecting the
    ``cf_clearance`` entry from a multi-cookie string), and the User-Agent from a
    ``-H 'User-Agent: ...'`` header or an ``-A``/``--user-agent`` value. Header names are matched
    case-insensitively; the last occurrence of each field wins. Raises :class:`CurlParseError` if
    either half is missing or the text cannot be tokenized.
    """
    try:
        tokens = shlex.split(curl_text)
    except ValueError as exc:
        raise CurlParseError(_UNPARSEABLE) from exc

    cf_clearance: str | None = None
    user_agent: str | None = None

    index = 0
    while index < len(tokens):
        token = tokens[index]
        value = tokens[index + 1] if index + 1 < len(tokens) else None
        if value is not None and token in ("-H", "--header"):
            name, _, raw = value.partition(":")
            key = name.strip().lower()
            if key == "cookie":
                cf_clearance = _cf_from_cookie(raw) or cf_clearance
            elif key == "user-agent":
                user_agent = raw.strip() or user_agent
            index += 2
            continue
        if value is not None and token in ("-b", "--cookie"):
            cf_clearance = _cf_from_cookie(value) or cf_clearance
            index += 2
            continue
        if value is not None and token in ("-A", "--user-agent"):
            user_agent = value.strip() or user_agent
            index += 2
            continue
        index += 1

    if cf_clearance is None:
        raise CurlParseError(_NO_CLEARANCE)
    if not user_agent:
        raise CurlParseError(_NO_UA)
    return cf_clearance, user_agent


def _cf_from_cookie(cookie_str: str) -> str | None:
    """Pick the ``cf_clearance`` value out of a cookie string (``a=1; cf_clearance=tok; b=2``)."""
    for part in cookie_str.split(";"):
        name, sep, raw = part.strip().partition("=")
        if sep and name.strip() == _CF_COOKIE:
            return raw.strip() or None
    return None
