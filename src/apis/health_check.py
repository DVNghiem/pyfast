# -*- coding: utf-8 -*-
from src.core import HTTPEndpoint
from starlette.requests import Request
from src.core.cache import Cache, CacheTag
from src.core.graphql import GraphQL
from typing import Optional

from pydantic import BaseModel


class Test(BaseModel):
	test1: Optional[str] = None


class HealthCheck(HTTPEndpoint):
	@Cache.cached(tag=CacheTag.GET_HEALTH_CHECK, ttl=120, identify={'query_params': ['test1']})  # type: ignore
	async def get(self, _request: Request, _query_params: Test) -> dict:
		"""
		Health Check
		"""
		return {'status': 'ok'}


class HealthCheckGraphQL(GraphQL):
	object_type = 'Query'

	def resolve_health_check(self, request: Request, data: Test) -> str:
		return 'health_check ok'
