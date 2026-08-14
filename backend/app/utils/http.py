"""Shared async HTTP client used by scanners."""
from __future__ import annotations

import httpx
from app.config import settings

_client: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.http_timeout),
            follow_redirects=False,
            headers={"User-Agent": settings.user_agent},
            verify=True,
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
        )
    return _client


async def close_http_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
