"""Keenable SDK client with bounded, header-aware rate-limit retries."""

import asyncio
from contextvars import ContextVar
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx
from keenable import AsyncKeenable, KeenableRateLimitError


def _retry_delay(header):
    if not header:
        return None
    header = header.strip()
    if header.isascii() and header.isdigit() and len(header) <= 6:
        return int(header)
    try:
        retry_at = parsedate_to_datetime(header)
        if retry_at.utcoffset() is None:
            return None
        return max(0, (retry_at - datetime.now(timezone.utc)).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return None


class RetryingKeenable:
    def __init__(self, *, api_key, transport=None, sleep=asyncio.sleep):
        self._retry_after = ContextVar("keenable_retry_after", default=None)
        self._sleep = sleep
        # HTTPX response hooks run before the SDK discards response headers.
        # https://www.python-httpx.org/advanced/event-hooks/
        self._http = httpx.AsyncClient(
            timeout=30, transport=transport,
            event_hooks={"response": [self._capture_retry_after]},
        )
        self._client = AsyncKeenable(api_key=api_key, client=self._http,
                                     client_source="SF Promises")

    async def _capture_retry_after(self, response):
        self._retry_after.set(response.headers.get("Retry-After") if response.status_code == 429 else None)

    async def _request(self, method, *args, **kwargs):
        token = self._retry_after.set(None)
        try:
            for attempt in range(3):
                self._retry_after.set(None)
                try:
                    return await method(*args, **kwargs)
                except KeenableRateLimitError:
                    delay = _retry_delay(self._retry_after.get())
                    if attempt == 2 or delay is None or delay > 30:
                        raise
                    await self._sleep(delay)
        finally:
            self._retry_after.reset(token)

    async def search(self, *args, **kwargs):
        return await self._request(self._client.search, *args, **kwargs)

    async def fetch(self, *args, **kwargs):
        return await self._request(self._client.fetch, *args, **kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self._http.aclose()
