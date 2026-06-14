"""Configuration for the vgmdb transport."""

from __future__ import annotations

from pydantic import BaseModel, Field

DEFAULT_BASE_URL = "https://vgmdb.net"


class TransportConfig(BaseModel):
    """Settings for a vgmdb transport client.

    ``user_agent`` is required and must match the browser the ``cf_clearance``
    token was issued for. A ``min_interval`` of ``0`` disables the politeness
    throttle.
    """

    base_url: str = DEFAULT_BASE_URL
    user_agent: str
    cf_clearance: str | None = None
    timeout: float = Field(default=10.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    backoff_base: float = Field(default=0.5, gt=0)
    backoff_max: float = Field(default=8.0, gt=0)
    min_interval: float = Field(default=1.0, ge=0)
    proxy: str | None = None
