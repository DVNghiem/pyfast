from src.apis.health_check import HealthCheck
from src.core.route import RouteSwagger
from starlette.routing import Route

__all__ = ["RouteSwagger"]

routes = [
    Route("/health_check", HealthCheck),
]
