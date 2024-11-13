# -*- coding: utf-8 -*-
from typing import Callable
import inspect

from hypern.caching.base import BaseKeyMaker


class CustomKeyMaker(BaseKeyMaker):
    async def make(self, function: Callable, prefix: str, identify_key: str = "") -> str:
        path = f"{prefix}:{inspect.getmodule(function).__name__}.{function.__name__}:{identify_key}"  # type: ignore
        return str(path)
