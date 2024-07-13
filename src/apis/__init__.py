# -*- coding: utf-8 -*-
from src.core.route import RouteSwagger
from src.apis.health_check import HealthCheck


routes = [RouteSwagger('/health_check', HealthCheck())]

__all__ = ['routes']
