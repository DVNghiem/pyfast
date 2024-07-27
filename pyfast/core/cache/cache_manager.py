# -*- coding: utf-8 -*-
from functools import wraps
from typing import Callable, Dict, Type

from .base import BaseBackend, BaseKeyMaker
from .cache_tag import CacheTag


class CacheManager:
    def __init__(self):
        self.backend = None
        self.key_maker = None

    def init(self, backend: BaseBackend, key_maker: BaseKeyMaker) -> None:
        self.backend = backend
        self.key_maker = key_maker

    def cached(self, tag: CacheTag, ttl: int = 60, identify: Dict = {}) -> Type[Callable]:
        def _cached(function):
            @wraps(function)
            async def __cached(*args, **kwargs):
                if not self.backend or not self.key_maker:
                    raise ValueError("Backend or KeyMaker not initialized")

                _identify_key = []
                for key, values in identify.items():
                    _obj = kwargs.get(key, None)
                    if not _obj:
                        raise Exception(f"Caching: Identify key {key} not found in kwargs")
                    for attr in values:
                        _identify_key.append(f"{attr}={getattr(_obj, attr)}")
                _identify_key = ":".join(_identify_key)

                key = await self.key_maker.make(function=function, prefix=tag.value, identify_key=_identify_key)

                cached_response = await self.backend.get(key=key)
                if cached_response:
                    return cached_response

                response = await function(*args, **kwargs)
                await self.backend.set(response=response, key=key, ttl=ttl)
                return response

            return __cached

        return _cached  # type: ignore

    async def remove_by_tag(self, tag: CacheTag) -> None:
        await self.backend.delete_startswith(value=tag.value)

    async def remove_by_prefix(self, prefix: str) -> None:
        await self.backend.delete_startswith(value=prefix)


Cache = CacheManager()
