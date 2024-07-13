# -*- coding: utf-8 -*-
from robyn import Request
from src.enum import ErrorCode
from src.core.exception import Forbidden
from abc import ABC, abstractmethod
from src.core.logger import logger
from src.config import config
import datetime
import jwt
import traceback
import typing


class Authorization(ABC):
	def __init__(self) -> None:
		super().__init__()
		self.auth_data = None
		self.name = 'base'

	@abstractmethod
	def validate(self, request: Request, *arg, **kwargs) -> typing.Any:
		pass
