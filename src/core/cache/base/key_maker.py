# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Callable


class BaseKeyMaker(ABC):
	@abstractmethod
	async def make(self, function: Callable, prefix: str, identify_key: str) -> str: ...
