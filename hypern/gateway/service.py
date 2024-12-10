from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ServiceStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


@dataclass
class ServiceConfig:
    name: str
    url: str
    prefix: str
    timeout: float = 30.0
    max_retries: int = 3
    health_check_path: str = "/health"


class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, ServiceConfig] = {}
        self._status: Dict[str, ServiceStatus] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(self, service: ServiceConfig, metadata: Optional[Dict[str, Any]] = None):
        self._services[service.name] = service
        self._status[service.name] = ServiceStatus.ONLINE
        self._metadata[service.name] = metadata or {}

    def unregister(self, service_name: str):
        self._services.pop(service_name, None)
        self._status.pop(service_name, None)
        self._metadata.pop(service_name, None)

    def get_service(self, service_name: str) -> Optional[ServiceConfig]:
        return self._services.get(service_name)

    def get_service_by_prefix(self, path: str) -> Optional[ServiceConfig]:
        for service in self._services.values():
            if path.startswith(service.prefix):
                return service
        return None

    def update_status(self, service_name: str, status: ServiceStatus):
        if service_name in self._services:
            self._status[service_name] = status

    def get_status(self, service_name: str) -> ServiceStatus:
        return self._status.get(service_name, ServiceStatus.OFFLINE)
