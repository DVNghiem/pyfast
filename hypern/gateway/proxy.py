import asyncio
from typing import Any, Dict, Optional

import aiohttp
import orjson
import traceback

from hypern.hypern import Request
from hypern.response import JSONResponse

from .service import ServiceConfig, ServiceRegistry, ServiceStatus


class Proxy:
    def __init__(self, service_registry: ServiceRegistry):
        self._registry = service_registry
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiters: Dict[str, asyncio.Semaphore] = {}

    async def startup(self):
        self._session = aiohttp.ClientSession()
        for service in self._registry._services.values():
            self._rate_limiters[service.name] = asyncio.Semaphore(100)  # Default 100 concurrent requests

    async def shutdown(self):
        if self._session:
            await self._session.close()

    async def forward_request(self, service: ServiceConfig, request: Request) -> Any:
        if not self._session:
            await self.startup()

        target_path = request.path.replace(service.prefix, "", 1)
        target_url = f"{service.url}{target_path}"

        headers = request.headers.get_headers()
        # Remove hop-by-hop headers
        for header in ["connection", "keep-alive", "transfer-encoding"]:
            headers.pop(header, None)

        async with self._rate_limiters[service.name]:
            try:
                async with self._session.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    params=request.query_params.to_dict(),
                    data=await request.json() if request.method in ["POST", "PUT", "PATCH"] else None,
                    timeout=aiohttp.ClientTimeout(total=service.timeout),
                ) as response:
                    body = await response.read()
                    return JSONResponse(
                        content=orjson.loads(body) if response.content_type == "application/json" else body.decode(),
                        status_code=response.status,
                        headers=dict(response.headers),
                    )
            except Exception as e:
                traceback.print_exc()
                self._registry.update_status(service.name, ServiceStatus.DEGRADED)
                return JSONResponse(content={"error": "Service unavailable", "details": str(e)}, status_code=503)
