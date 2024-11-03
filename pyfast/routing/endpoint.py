# -*- coding: utf-8 -*-
from __future__ import annotations

from robyn import Request, Response
from pydantic import BaseModel, ValidationError
from pyfast.exceptions import BadRequest, BaseException, ValidationError as PyfastValidationError
from pyfast.auth.authorization import Authorization
from pyfast.response import JSONResponse
from pydash import get
import typing
import asyncio
import functools
import inspect
import orjson
import traceback


def is_async_callable(obj: typing.Any) -> bool:
    while isinstance(obj, functools.partial):
        obj = obj.func

    return asyncio.iscoroutinefunction(obj) or (callable(obj) and asyncio.iscoroutinefunction(obj.__call__))


async def run_in_threadpool(func: typing.Callable, *args, **kwargs):
    if kwargs:  # pragma: no cover
        # run_sync doesn't accept 'kwargs', so bind them in here
        func = functools.partial(func, **kwargs)
    return await asyncio.to_thread(func, *args)


class ParamParser:
    def __init__(self, request):
        self.request = request

    def parse_data_by_name(self, param_name: str) -> dict:
        param_name = param_name.lower()
        data_parsers = {
            "query_params": lambda: self.request.query_params.to_dict(),
            "path_params": lambda: dict(self.request.path_params.items()),
            "form_data": self._parse_form_data,
        }

        parser = data_parsers.get(param_name)
        if not parser:
            raise BadRequest(msg="Backend Error: Invalid parameter type, must be query_params, path_params or form_data.")

        return parser()

    def _parse_form_data(self) -> dict:
        form_data = {k: v for k, v in self.request.form_data.items()}
        return form_data if form_data else self.request.json()


class InputHandler:
    def __init__(self, request, global_dependencies, router_dependencies):
        self.request = request
        self.global_dependencies = global_dependencies
        self.router_dependencies = router_dependencies
        self.param_parser = ParamParser(request)

    async def parse_pydantic_model(self, param_name: str, model_class: typing.Type[BaseModel]) -> BaseModel:
        try:
            data = self.param_parser.parse_data_by_name(param_name)
            return model_class(**data)
        except ValidationError as e:
            invalid_fields = orjson.loads(e.json())
            raise PyfastValidationError(
                msg=orjson.dumps(
                    [
                        {
                            "field": get(item, "loc")[0],
                            "msg": get(item, "msg"),
                        }
                        for item in invalid_fields
                    ]
                ).decode("utf-8"),
            )

    async def handle_special_params(self, param_name: str) -> typing.Any:
        special_params = {
            "request": lambda: self.request,
            "global_dependencies": lambda: self.global_dependencies,
            "router_dependencies": lambda: self.router_dependencies,
        }
        return special_params.get(param_name, lambda: None)()

    async def get_input_handler(self, signature: inspect.Signature) -> typing.Dict[str, typing.Any]:
        """
        Parse the request data and return the kwargs for the handler
        """
        kwargs = {}

        for param in signature.parameters.values():
            name = param.name
            ptype = param.annotation

            # Handle Pydantic models
            if isinstance(ptype, type) and issubclass(ptype, BaseModel):
                kwargs[name] = await self.parse_pydantic_model(name, ptype)
                continue

            # Handle Authorization
            if isinstance(ptype, type) and issubclass(ptype, Authorization):
                kwargs[name] = await ptype().validate(self.request)
                continue

            # Handle special parameters
            special_value = await self.handle_special_params(name)
            if special_value is not None:
                kwargs[name] = special_value

        return kwargs


class HTTPEndpoint:
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def method_not_allowed(self, request: Request) -> Response:
        return JSONResponse(
            description=orjson.dumps({"data": "", "errors": "Method Not Allowed", "error_code": 405}),
            status_code=405,
        )

    async def get_input_handler(self, signature: inspect.Signature, request: Request, global_dependencies, router_dependencies) -> typing.Dict[str, typing.Any]:
        """
        This function will parse the request data and return the kwargs for the handler

        params:
            signature: The function signature
            request: Request -> The request object
        """
        handler = InputHandler(request, global_dependencies, router_dependencies)
        return await handler.get_input_handler(signature)

    async def dispatch(self, request: Request, global_dependencies, router_dependencies) -> None:
        handler_name = "get" if request.method == "HEAD" and not hasattr(self, "head") else request.method.lower()
        handler: typing.Callable[[Request], typing.Any] = getattr(  # type: ignore
            self, handler_name, self.method_not_allowed
        )
        try:
            is_async = is_async_callable(handler)
            signature = inspect.signature(handler)
            _response_type = signature.return_annotation
            _kwargs = await self.get_input_handler(signature, request, global_dependencies, router_dependencies)

            if is_async:
                response = await handler(**_kwargs)  # type: ignore
            else:
                response = await run_in_threadpool(handler, **_kwargs)
            if not isinstance(response, Response):
                if isinstance(_response_type, type) and issubclass(_response_type, BaseModel):
                    response = _response_type.model_validate(response).model_dump(mode="json")  # type: ignore
                response = JSONResponse(
                    content=orjson.dumps({"message": response, "error_code": None}),
                    status_code=200,
                )

        except Exception as e:
            _res: typing.Dict = {"message": "", "error_code": "UNKNOWN_ERROR"}
            if isinstance(e, BaseException):
                _res["error_code"] = e.error_code
                _res["message"] = e.msg
                _status = e.status
            else:
                traceback.print_exc()
                _res["message"] = str(e)
                _status = 400
            response = JSONResponse(
                content=orjson.dumps(_res),
                status_code=_status,
            )
        return response
