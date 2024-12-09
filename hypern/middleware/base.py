from typing import Optional
from hypern.hypern import MiddlewareConfig


class Middleware:
    def __init__(self, config: Optional[MiddlewareConfig] = None):
        self.config = config or MiddlewareConfig.default()

    async def before_request(self, request):
        return request

    async def after_request(self, response):
        return response
