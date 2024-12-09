from abc import ABC, abstractmethod
from typing import Any


class BaseBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any: ...

    @abstractmethod
    async def set(self, response: Any, key: str, ttl: int = 60) -> None: ...

    @abstractmethod
    async def delete_pattern(self, pattern: str) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...

    @abstractmethod
    async def set_nx(self, response: Any, key: str, ttl: int = 60) -> bool: ...

    @abstractmethod
    async def ttl(self, key: str) -> int: ...

    @abstractmethod
    async def incr(self, key: str) -> int: ...

    @abstractmethod
    async def clear(self) -> None: ...
