# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel
from ariadne import ObjectType, make_executable_schema as mes
from typing import Callable
from functools import wraps
from starlette.concurrency import run_in_threadpool

import asyncio
import inspect


def make_executable_schema(type_defs, resolvers, snake_case_fallback_resolvers):
	_migrate_resolvers = []
	for resolver in resolvers:
		_migrate_resolvers.append(resolver()())
	return mes(type_defs, _migrate_resolvers, snake_case_fallback_resolvers)


class GraphQL:
	object_type: Optional[str] = None

	def __call__(self, *args: Any, **kwds: Any) -> Any:
		if not self.object_type:
			raise Exception('object_type is not defined')
		_object = ObjectType(self.object_type)
		_methods = inspect.getmembers(self, predicate=inspect.ismethod)
		for name, resolve in _methods:
			if name.startswith('resolve_'):
				_object.set_field(
					name=name.replace('resolve_', ''), resolver=self.decorated(resolve)
				)
		return _object

	def decorated(self, func: Callable[..., Any]) -> Any:
		@wraps(func)
		async def wrapper(*args: Any, **kwds: Any) -> Any:
			_request = args[1].context.get('request')

			signature = inspect.signature(func)
			_kwargs = {}
			for param in signature.parameters.values():
				name = param.name
				ptype = param.annotation
				if name == 'request':
					_kwargs[name] = _request
				elif name == 'data':
					if isinstance(ptype, type) and issubclass(ptype, BaseModel):
						_kwargs[name] = ptype(**kwds)
					else:
						raise Exception('Invalid parameter type')
				else:
					raise Exception('Invalid parameter name')
			if asyncio.iscoroutinefunction(func):
				return await func(**_kwargs)
			return await run_in_threadpool(func, **_kwargs)

		return wrapper
