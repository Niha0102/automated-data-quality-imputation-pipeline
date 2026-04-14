from redis.asyncio import Redis, from_url
from app.core.config import settings

_redis: Redis | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


# ── Cache helpers ─────────────────────────────────────────────────────────────

PROFILE_TTL = 7_200       # 2 hours
JOB_STATUS_TTL = 86_400   # 24 hours
SESSION_TTL = 604_800     # 7 days
RATE_LIMIT_TTL = 60       # 1 minute


async def cache_set(key: str, value: str, ttl: int) -> None:
    await get_redis().setex(key, ttl, value)


async def cache_get(key: str) -> str | None:
    return await get_redis().get(key)


async def cache_delete(key: str) -> None:
    await get_redis().delete(key)


async def increment_rate_limit(user_id: str) -> int:
    """Increment request counter for user; returns new count. Sets TTL on first call."""
    key = f"rate_limit:{user_id}"
    redis = get_redis()
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, RATE_LIMIT_TTL)
    return count
