import inspect
from typing import Callable

from src.core.cache.base import BaseKeyMaker


class CustomKeyMaker(BaseKeyMaker):
    async def make(
        self, function: Callable, prefix: str, identify_key: str = ""
    ) -> str:
        path = f"{prefix}:{inspect.getmodule(function).__name__}.{function.__name__}:{identify_key}"
        return path
