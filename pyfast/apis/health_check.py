# -*- coding: utf-8 -*-
from robyn import Request
from typing import Optional
from pydantic import BaseModel
from pyfast.core import HTTPEndpoint
from pyfast.core.cache import Cache, CacheTag


class Test(BaseModel):
    test1: Optional[str] = None


class HealthCheck(HTTPEndpoint):
    @Cache.cached(tag=CacheTag.GET_HEALTH_CHECK)
    async def get(self, request: Request, query_params: Test) -> dict:
        """
        Health Check
        """
        return {"status": "ok"}
