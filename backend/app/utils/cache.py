"""Redis-backed cache with an in-memory fallback for environments without Redis.

Both backends expose the same minimal async API so the rest of the app is
agnostic to the underlying store.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger("aegis.cache")


class _MemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}

    async def get(self, key: str) -> Optional[str]:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires, value = entry
        if expires < time.time():
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: str, ttl: int = None) -> None:
        ttl = ttl or settings.cache_default_ttl
        self._store[key] = (time.time() + ttl, value)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def flush(self) -> None:
        self._store.clear()


class _RedisCache:
    def __init__(self) -> None:
        import redis.asyncio as redis

        self._client = redis.from_url(
            settings.redis_url, decode_responses=True, socket_connect_timeout=2
        )

    async def get(self, key: str) -> Optional[str]:
        try:
            return await self._client.get(key)
        except Exception:  # pragma: no cover - redis down
            logger.warning("redis unavailable, falling back to memory")
            return None

    async def set(self, key: str, value: str, ttl: int = None) -> None:
        ttl = ttl or settings.cache_default_ttl
        try:
            await self._client.set(key, value, ex=ttl)
        except Exception:  # pragma: no cover
            logger.warning("redis unavailable, falling back to memory")

    async def delete(self, key: str) -> None:
        try:
            await self._client.delete(key)
        except Exception:  # pragma: no cover
            pass

    async def flush(self) -> None:
        try:
            await self._client.flushdb()
        except Exception:  # pragma: no cover
            pass


_cache: Optional[Any] = None


def get_cache() -> Any:
    global _cache
    if _cache is None:
        if settings.redis_url.startswith(("redis://", "rediss://")):
            try:
                _cache = _RedisCache()
            except Exception:  # pragma: no cover
                _cache = _MemoryCache()
        else:
            _cache = _MemoryCache()
    return _cache


async def cache_get_json(key: str) -> Any:
    raw = await get_cache().get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def cache_set_json(key: str, value: Any, ttl: int = None) -> None:
    await get_cache().set(key, json.dumps(value, default=str), ttl=ttl)
