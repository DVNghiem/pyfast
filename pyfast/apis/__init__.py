# -*- coding: utf-8 -*-
from pyfast.core.route import RouteSwagger
from pyfast.apis.health_check import HealthCheck


routes = [RouteSwagger("/health_check", HealthCheck)]

__all__ = ["routes"]
