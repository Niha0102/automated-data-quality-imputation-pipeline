"""In-memory Redis stub for local dev without a Redis server."""
from __future__ import annotations
import asyncio
from typing import Optional


class _StubRedis:
    def __init__(self):
        self._store: dict = {}

    async def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._store[key] = value

    async def set(self, key: str, value: str) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def incr(self, key: str) -> int:
        val = int(self._store.get(key, 0)) + 1
        self._store[key] = str(val)
        return val

    async def expire(self, key: str, ttl: int) -> None:
        pass  # no-op in stub

    async def publish(self, channel: str, message: str) -> None:
        pass  # no-op in stub

    async def aclose(self) -> None:
        pass


_stub = _StubRedis()


def get_stub_redis() -> _StubRedis:
    return _stub
