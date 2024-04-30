# -*- coding: utf-8 -*-
from src.apis.health_check import HealthCheck, HealthCheckGraphQL
from src.core.route import RouteSwagger
from starlette.routing import Route


routes = [
	Route('/health_check', HealthCheck),
]

graphql_route = [HealthCheckGraphQL]

__all__ = ['routes', 'RouteSwagger', 'graphql_route']
