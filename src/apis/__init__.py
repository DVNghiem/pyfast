# -*- coding: utf-8 -*-
from src.apis.health_check import HealthCheck
from src.core.route import RouteSwagger
from starlette.routing import Route


routes = [
	Route('/health_check', HealthCheck),
]


__all__ = ['routes', 'RouteSwagger']
