# -*- coding: utf-8 -*-
from pyfast.core.route import RouteSwagger
from pyfast.apis.health_check import HealthCheck
from pyfast.apis.benchmark import routes as benchmark_routes


routes = [RouteSwagger("/health_check", HealthCheck), *benchmark_routes]

__all__ = ["routes"]
