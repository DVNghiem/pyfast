from src.core import HTTPEndpoint
from starlette.requests import Request
from src.core.cache import Cache, CacheTag
from typing import Optional

from pydantic import BaseModel


class Test(BaseModel):
    test1: Optional[str] = None
    test2: Optional[str] = None


class HealthCheck(HTTPEndpoint):
    @Cache.cached(
        tag=CacheTag.GET_HEALTH_CHECK, ttl=120, identify={"query_params": ["test1"]}
    )
    async def get(self, request: Request, query_params: Test) -> dict:
        """
        Health Check
        """
        return {"status": "ok"}
