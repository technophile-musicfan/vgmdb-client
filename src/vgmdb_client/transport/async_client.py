"""Asynchronous vgmdb transport over httpx.AsyncClient."""

from __future__ import annotations

import asyncio
import logging
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

logger = logging.getLogger(__name__)


class AsyncTransport:
    """Authenticated, Cloudflare-aware asynchronous fetcher for vgmdb pages."""

    def __init__(self, config: TransportConfig) -> None:
        self._config = config
        self._last: float | None = None
        self._throttle_lock = asyncio.Lock()
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
        retrying = build_async_retrying(self._config)
        attempt = 0

        async def _attempt() -> str:
            nonlocal attempt
            attempt += 1
            await self._throttle()  # space every HTTP attempt, including retries
            try:
                response = await self._client.get(path)
            except httpx.TransportError as exc:
                logger.debug("GET %s failed on attempt %d: %r", path, attempt, exc)
                raise TransientTransportError from exc
            logger.debug("GET %s -> %s (attempt %d)", path, response.status_code, attempt)
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
        # Serialize the gate so concurrent get() coroutines honor min_interval instead of
        # racing on self._last; each waits its turn behind the previous request.
        async with self._throttle_lock:
            wait = throttle_wait(self._last, time.monotonic(), interval)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.monotonic()
