# -*- coding: utf-8 -*-
from src.core import HTTPEndpoint
from robyn import Request
from typing import Optional

from pydantic import BaseModel


class Test(BaseModel):
	test1: Optional[str] = None


class HealthCheck(HTTPEndpoint):

	async def get(self, request: Request, query_params: Test) -> dict:
		"""
		Health Check
		"""
		return {'status': 'ok'}
