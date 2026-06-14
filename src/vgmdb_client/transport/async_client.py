"""Asynchronous vgmdb transport over httpx.AsyncClient."""

from __future__ import annotations

import asyncio
import time
from types import TracebackType

import httpx

from vgmdb_client.transport.config import TransportConfig
from vgmdb_client.transport.core import (
    CF_COOKIE_NAME,
    build_async_retrying,
    build_cookies,
    build_headers,
    classify_response,
    throttle_wait,
)
from vgmdb_client.transport.errors import TransientTransportError


class AsyncTransport:
    """Authenticated, Cloudflare-aware asynchronous fetcher for vgmdb pages."""

    def __init__(self, config: TransportConfig) -> None:
        self._config = config
        self._last: float | None = None
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            headers=build_headers(config.user_agent),
            cookies=build_cookies(config.cf_clearance),
            timeout=config.timeout,
            proxy=config.proxy,
            follow_redirects=True,
        )

    async def get(self, path: str) -> str:
        """Fetch ``path`` and return the HTML body, or raise a typed transport error."""
        await self._throttle()
        retrying = build_async_retrying(self._config)

        async def _attempt() -> str:
            try:
                response = await self._client.get(path)
            except httpx.TransportError as exc:
                raise TransientTransportError from exc
            classify_response(response.status_code, response.headers, response.text)
            return response.text

        result: str = await retrying(_attempt)
        return result

    def set_cf_clearance(self, token: str) -> None:
        """Update the cf_clearance cookie used by subsequent requests."""
        self._config.cf_clearance = token
        self._client.cookies.set(CF_COOKIE_NAME, token)

    def set_user_agent(self, user_agent: str) -> None:
        """Update the User-Agent header used by subsequent requests."""
        self._config.user_agent = user_agent
        self._client.headers["User-Agent"] = user_agent

    async def aclose(self) -> None:
        await self._client.aclose()

    @property
    def is_closed(self) -> bool:
        return self._client.is_closed

    async def __aenter__(self) -> AsyncTransport:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def _throttle(self) -> None:
        interval = self._config.min_interval
        if interval <= 0:
            return
        wait = throttle_wait(self._last, time.monotonic(), interval)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last = time.monotonic()
