# -*- coding: utf-8 -*-
from robyn import Request
from abc import ABC, abstractmethod
import typing


class Authorization(ABC):
    def __init__(self) -> None:
        super().__init__()
        self.auth_data = None
        self.name = "base"

    @abstractmethod
    def validate(self, request: Request, *arg, **kwargs) -> typing.Any:
        pass
