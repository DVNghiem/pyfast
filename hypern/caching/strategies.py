from typing import Any, Optional, Callable, TypeVar
from datetime import datetime
import asyncio
import orjson

from hypern.logging import logger

T = TypeVar("T")


class CacheEntry:
    def __init__(self, value: Any, expires_at: int, stale_at: Optional[int] = None):
        self.value = value
        self.expires_at = expires_at
        self.stale_at = stale_at or expires_at
        self.is_revalidating = False

    def to_json(self) -> str:
        return orjson.dumps({"value": self.value, "expires_at": self.expires_at, "stale_at": self.stale_at, "is_revalidating": self.is_revalidating})

    @classmethod
    def from_json(cls, data: str) -> "CacheEntry":
        data_dict = orjson.loads(data)
        entry = cls(value=data_dict["value"], expires_at=data_dict["expires_at"], stale_at=data_dict["stale_at"])
        entry.is_revalidating = data_dict["is_revalidating"]
        return entry


class CacheStrategy:
    def __init__(self, backend: Any):
        self.backend = backend

    async def get(self, key: str, loader: Callable[[], T]) -> T:
        raise NotImplementedError


class StaleWhileRevalidateStrategy(CacheStrategy):
    def __init__(self, backend: Any, stale_ttl: int, cache_ttl: int):
        super().__init__(backend)
        self.stale_ttl = stale_ttl
        self.cache_ttl = cache_ttl

    async def get(self, key: str, loader: Callable[[], T]) -> T:
        now = int(datetime.now().timestamp())

        # Try to get from cache
        cached_data = await self.backend.get(key)
        if cached_data:
            entry = CacheEntry.from_json(cached_data)

            if now < entry.stale_at:
                # Cache is fresh
                return entry.value

            if now < entry.expires_at and not entry.is_revalidating:
                # Cache is stale but usable - trigger background revalidation
                entry.is_revalidating = True
                await self.backend.set(key, entry.to_json(), self.cache_ttl)
                asyncio.create_task(self._revalidate(key, loader))
                return entry.value

        # Cache miss or expired - load fresh data
        value = await loader()
        entry = CacheEntry(value=value, expires_at=now + self.cache_ttl, stale_at=now + (self.cache_ttl - self.stale_ttl))
        await self.backend.set(key, entry.to_json(), self.cache_ttl)
        return value

    async def _revalidate(self, key: str, loader: Callable[[], T]):
        try:
            value = await loader()
            now = int(datetime.now().timestamp())
            entry = CacheEntry(value=value, expires_at=now + self.cache_ttl, stale_at=now + (self.cache_ttl - self.stale_ttl))
            await self.backend.set(key, entry.to_json(), self.cache_ttl)
        except Exception as e:
            logger.error(f"Revalidation failed for key {key}: {e}")


class CacheAsideStrategy(CacheStrategy):
    def __init__(self, backend: Any, ttl: int):
        super().__init__(backend)
        self.ttl = ttl

    async def get(self, key: str, loader: Callable[[], T]) -> T:
        # Try to get from cache
        cached_data = await self.backend.get(key)
        if cached_data:
            entry = CacheEntry.from_json(cached_data)
            if entry.expires_at > int(datetime.now().timestamp()):
                return entry.value

        # Cache miss or expired - load from source
        value = await loader()
        entry = CacheEntry(value=value, expires_at=int(datetime.now().timestamp()) + self.ttl)
        await self.backend.set(key, entry.to_json(), self.ttl)
        return value


def cache_with_strategy(strategy: CacheStrategy, key_prefix: str = None):
    """
    Decorator for using cache strategies
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix or func.__name__}:{hash(str(args) + str(kwargs))}"

            async def loader():
                return await func(*args, **kwargs)

            return await strategy.get(cache_key, loader)

        return wrapper

    return decorator
