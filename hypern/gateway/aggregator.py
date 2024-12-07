import asyncio
from typing import Any, Dict, List

from hypern.response import JSONResponse

from .proxy import Proxy
from .service import ServiceRegistry


class Aggregator:
    def __init__(self, registry: ServiceRegistry, proxy: Proxy):
        self._registry = registry
        self._proxy = proxy

    async def aggregate_responses(self, requests: List[Dict[str, Any]]) -> JSONResponse:
        tasks = []
        for req in requests:
            service = self._registry.get_service(req["service"])
            if service:
                tasks.append(self._proxy.forward_request(service, req["request"]))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        aggregated = {}
        for i, response in enumerate(responses):
            service_name = requests[i]["service"]
            if isinstance(response, Exception):
                aggregated[service_name] = {"status": "error", "error": str(response)}
            else:
                aggregated[service_name] = {"status": "success", "data": response.body}

        return JSONResponse(content=aggregated)
