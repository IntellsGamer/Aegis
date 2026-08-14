"""Rate limiting: fixed-window counters.

Supports both an async backend (used inside async code paths) and a
synchronous backend (used by the Flask request hooks).
"""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int = 0


class _WindowCounter:
    """Thread-safe fixed-window counter in pure Python (no external deps)."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[int, float]] = {}
        self._lock = None

    def _ensure_lock(self):
        if self._lock is None:
            import threading

            self._lock = threading.Lock()
        return self._lock

    def hit(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        now = time.time()
        window = int(now // window_seconds)
        bucket = f"{key}:{window}"
        with self._ensure_lock():
            entry = self._store.get(bucket)
            if entry is None:
                self._store[bucket] = (1, now)
                self._prune(now)
                return RateLimitResult(True, limit, limit - 1)
            count, _started = entry
            if count >= limit:
                retry_after = int(window_seconds - (now % window_seconds))
                return RateLimitResult(False, limit, 0, retry_after)
            self._store[bucket] = (count + 1, now)
            return RateLimitResult(True, limit, limit - count - 1)

    def _prune(self, now: float) -> None:
        stale = [k for k, (_, ts) in self._store.items() if now - ts > 300]
        for key in stale:
            self._store.pop(key, None)


_async_cache: object | None = None
_sync_counter = _WindowCounter()

# Optionally mirror async bucket writes into Redis when available.
_REDIS = None


def _get_async_cache():
    global _async_cache
    if _async_cache is None:
        from app.utils.cache import get_cache

        _async_cache = get_cache()
    return _async_cache


async def check_rate_limit(key: str, limit: int, window_seconds: int = 60) -> RateLimitResult:
    """Async variant for use inside async scanners/tasks."""
    cache = await _get_async_cache_awaitable()
    bucket = f"rl:{window_seconds}:{key}"
    now = int(time.time())
    window_key = f"{bucket}:{now // window_seconds}"
    count_raw = await cache.get(window_key)
    count = int(count_raw) if count_raw else 0
    if count >= limit:
        retry_after = window_seconds - (now % window_seconds)
        return RateLimitResult(False, limit, 0, retry_after)
    await cache.set(window_key, str(count + 1), ttl=window_seconds)
    return RateLimitResult(True, limit, limit - count - 1)


async def _get_async_cache_awaitable():
    return _get_async_cache()


def check_rate_limit_sync(key: str, limit: int, window_seconds: int = 60) -> RateLimitResult:
    """Synchronous variant for Flask request hooks."""
    if limit <= 0:
        return RateLimitResult(True, 0, 0)
    return _sync_counter.hit(key, limit, window_seconds)


def client_key(request, extra: str = "") -> str:
    """Build a rate-limit key from client IP + optional dimension."""
    ip = request.remote_addr or "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    return f"{ip}:{extra}".strip(":")
