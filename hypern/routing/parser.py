# -*- coding: utf-8 -*-
from __future__ import annotations

from pydantic import BaseModel, ValidationError
from robyn import Request
from hypern.exceptions import BadRequest, ValidationError as HypernValidationError
from hypern.auth.authorization import Authorization
from pydash import get
import typing
import inspect
import orjson


class ParamParser:
    def __init__(self, request: Request):
        self.request = request

    def parse_data_by_name(self, param_name: str) -> dict:
        param_name = param_name.lower()
        data_parsers = {
            "query_params": self._parse_query_params,
            "path_params": self._parse_path_params,
            "form_data": self._parse_form_data,
        }

        parser = data_parsers.get(param_name)
        if not parser:
            raise BadRequest(msg="Backend Error: Invalid parameter type, must be query_params, path_params or form_data.")
        return parser()

    def _parse_query_params(self) -> dict:
        query_params = self.request.query_params.to_dict()
        return {k: v[0] for k, v in query_params.items()}

    def _parse_path_params(self) -> dict:
        return lambda: dict(self.request.path_params.items())

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
            raise HypernValidationError(
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
