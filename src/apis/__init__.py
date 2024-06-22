# -*- coding: utf-8 -*-
from starlette.routing import Route
from src.core.route import RouteSwagger
from src.apis.health_check import HealthCheck
from src.apis.user import UserAPI


routes = [Route('/health_check', HealthCheck), RouteSwagger('/user', UserAPI, tags=['User'])]


__all__ = ['routes', 'RouteSwagger']
