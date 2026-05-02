"""Async Redis clients (cache + pub/sub)."""

from __future__ import annotations

from redis.asyncio import Redis, from_url

from .config import get_settings

_settings = get_settings()

_cache: Redis | None = None
_pubsub: Redis | None = None


async def get_cache() -> Redis:
    global _cache
    if _cache is None:
        _cache = from_url(
            _settings.redis_cache_url,
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30,
            max_connections=200,
        )
    return _cache


async def get_pubsub() -> Redis:
    global _pubsub
    if _pubsub is None:
        _pubsub = from_url(
            _settings.redis_channels_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=200,
        )
    return _pubsub


async def close_redis() -> None:
    global _cache, _pubsub
    if _cache is not None:
        await _cache.aclose()
        _cache = None
    if _pubsub is not None:
        await _pubsub.aclose()
        _pubsub = None
