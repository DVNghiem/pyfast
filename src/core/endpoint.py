# -*- coding: utf-8 -*-
from __future__ import annotations

from robyn import Request, Response, Headers
from pydantic import BaseModel, ValidationError
from src.core.exception import BadRequest, BaseException
from src.core.security import Authorization
from pydash import get
import sentry_sdk
import typing
import asyncio
import functools
import inspect
import ujson  # type: ignore
import traceback


def is_async_callable(obj: typing.Any) -> bool:
	while isinstance(obj, functools.partial):
		obj = obj.func

	return asyncio.iscoroutinefunction(obj) or (
		callable(obj) and asyncio.iscoroutinefunction(obj.__call__)
	)


async def run_in_threadpool(func: typing.Callable, *args, **kwargs):
	if kwargs:  # pragma: no cover
		# run_sync doesn't accept 'kwargs', so bind them in here
		func = functools.partial(func, **kwargs)
	return await asyncio.to_thread.run_sync(func, *args)


class HTTPEndpoint:
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)

	def method_not_allowed(self, request: Request) -> Response:
		return Response(
			description=ujson.dumps(
				{'data': '', 'errors': 'Method Not Allowed', 'error_code': 405}
			),
			headers=Headers({'Content-Type': 'application/json'}),
			status_code=405,
		)

	async def get_input_handler(
		self, signature: inspect.Signature, request: Request
	) -> typing.Dict[str, typing.Any]:
		"""
		This function will parse the request data and return the kwargs for the handler

		params:
		    handler: The handler function (get, post, put, delete, etc.)
		    request: Request -> The request object
		"""

		_kwargs = {}
		# inspect function to get the parameter names and types

		for param in signature.parameters.values():
			name = param.name
			ptype = param.annotation
			# if the parameter is a pydantic model, we will try to parse the request data
			if isinstance(ptype, type) and issubclass(ptype, BaseModel):
				_data = {}
				if name.lower() == 'query_params':
					_data = request.query_params.to_dict()
				elif name.lower() == 'path_params':
					_data = request.path_params.items()
				elif name.lower() == 'form_data':
					_data = await request.form_data.items()
					if not _data:
						_data = await request.json()
				else:
					raise BadRequest(
						msg='Backend Error: Invalid parameter type, must be query_params, path_params or form_data.'
					)
				try:
					_prams = ptype(**_data)
					_kwargs[name] = _prams
				except ValidationError as e:
					_invalid_fields = ujson.loads(e.json())
					raise BadRequest(
						errors=[
							{
								'field': get(item, 'loc')[0],
								'msg': get(item, 'msg'),
							}
							for item in _invalid_fields
						]
					)
			elif isinstance(ptype, type) and issubclass(ptype, Authorization):
				_kwargs[name] = await ptype().validate(request)
			elif name == 'request':
				_kwargs[name] = request
		return _kwargs

	async def dispatch(self, request: Request, *args, **kwargs) -> None:
		handler_name = (
			'get'
			if request.method == 'HEAD' and not hasattr(self, 'head')
			else request.method.lower()
		)
		handler: typing.Callable[[Request], typing.Any] = getattr(  # type: ignore
			self, handler_name, self.method_not_allowed
		)
		try:
			is_async = is_async_callable(handler)
			signature = inspect.signature(handler)
			_response_type = signature.return_annotation

			_kwargs = await self.get_input_handler(signature, request)

			if is_async:
				response = await handler(**_kwargs)  # type: ignore
			else:
				response = await run_in_threadpool(handler, **_kwargs)
			if not isinstance(response, Response):
				if isinstance(_response_type, type) and issubclass(_response_type, BaseModel):
					response = _response_type.model_validate(response).model_dump(mode='json')  # type: ignore
				response = Response(
					description=ujson.dumps({'data': response, 'errors': None, 'error_code': None}),
					headers=Headers({'Content-Type': 'application/json'}),
					status_code=200,
				)

		except Exception as e:
			_res: typing.Dict = {'data': ''}
			if isinstance(e, BaseException):
				_res['errors'] = e.errors
				_res['error_code'] = e.error_code
				_status = e.status
			else:
				traceback.print_exc()
				_res['errors'] = str(e)
				_status = 400
			if _status == 500:
				sentry_sdk.capture_exception()
				sentry_sdk.flush()
			response = Response(
				description=ujson.dumps(_res),
				headers=Headers({'Content-Type': 'application/json'}),
				status_code=_status,
			)
		return response
