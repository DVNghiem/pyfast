from typing import Any, Dict, List, Optional

from hypern import Hypern
from hypern.hypern import Request
from hypern.response import JSONResponse

from .aggregator import Aggregator
from .proxy import Proxy
from .service import ServiceConfig, ServiceRegistry


class APIGateway:
    def __init__(self, app: Hypern):
        self.app = app
        self.registry = ServiceRegistry()
        self.proxy = Proxy(self.registry)
        self.aggregator = Aggregator(self.registry, self.proxy)

    def register_service(self, config: ServiceConfig, metadata: Optional[Dict[str, Any]] = None):
        """Register a new service with the gateway"""
        self.registry.register(config, metadata)

    async def startup(self):
        """Initialize the gateway components"""
        await self.proxy.startup()

    async def shutdown(self):
        """Cleanup gateway resources"""
        await self.proxy.shutdown()

    async def handle_request(self, request: Request) -> Any:
        """Main request handler"""
        service = self.registry.get_service_by_prefix(request.path)
        if not service:
            return JSONResponse(content={"error": "Service not found"}, status_code=404)

        return await self.proxy.forward_request(service, request)

    async def aggregate(self, requests: List[Dict[str, Any]]) -> Any:
        """Handle aggregated requests"""
        return await self.aggregator.aggregate_responses(requests)
