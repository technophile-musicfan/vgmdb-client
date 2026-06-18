"""The ``(cf_clearance, User-Agent)`` credentials pair."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from vgmdb_client.auth.curl import parse_curl
from vgmdb_client.transport import TransportConfig

_EMPTY_FIELD = "must not be empty"


class Credentials(BaseModel):
    """An immutable ``cf_clearance`` token paired with the ``User-Agent`` it was issued for.

    The two travel together because a ``cf_clearance`` cookie is only valid with the exact
    ``User-Agent`` (and IP) it was minted for; pairing them prevents a mismatched, dead-on-arrival
    token. Construct from a browser paste with :meth:`from_curl`.
    """

    model_config = ConfigDict(frozen=True)

    cf_clearance: str
    user_agent: str

    @field_validator("cf_clearance", "user_agent")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(_EMPTY_FIELD)
        return value

    @classmethod
    def from_curl(cls, curl_text: str) -> Credentials:
        """Build credentials from a browser "Copy as cURL" paste.

        Raises :class:`~vgmdb_client.auth.errors.CurlParseError` if the paste lacks a
        ``cf_clearance`` cookie or a ``User-Agent``, or cannot be tokenized.
        """
        cf_clearance, user_agent = parse_curl(curl_text)
        return cls(cf_clearance=cf_clearance, user_agent=user_agent)

    def to_config(self, **overrides: Any) -> TransportConfig:
        """Build a :class:`TransportConfig` carrying this pair, forwarding extra config overrides
        (e.g. ``timeout``, ``min_interval``, ``proxy``)."""
        return TransportConfig(cf_clearance=self.cf_clearance, user_agent=self.user_agent, **overrides)
