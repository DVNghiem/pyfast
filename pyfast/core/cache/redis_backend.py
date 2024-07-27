# -*- coding: utf-8 -*-
import pickle
import ujson  # type: ignore

from typing import Any
import redis.asyncio as aioredis  # type: ignore
from pyfast.config import config
from pyfast.core.cache.base import BaseBackend

redis = aioredis.from_url(url=config.REDIS_URL)


class RedisBackend(BaseBackend):
    async def get(self, key: str) -> Any:
        result = await redis.get(key)
        if not result:
            return
        try:
            return ujson.loads(result.decode("utf8"))
        except UnicodeDecodeError:
            return pickle.loads(result)

    async def set(self, response: Any, key: str, ttl: int = 60) -> None:
        if isinstance(response, dict):
            response = ujson.dumps(response)
        elif isinstance(response, object):
            response = pickle.dumps(response)

        await redis.set(name=key, value=response, ex=ttl)

    async def delete_startswith(self, value: str) -> None:
        async for key in redis.scan_iter(f"{value}::*"):
            await redis.delete(key)
