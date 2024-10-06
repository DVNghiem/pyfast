# -*- coding: utf-8 -*-
from typing import Callable, Any, Dict, List, Union, get_origin, get_args
from robyn.router import Router, Route
from robyn import HttpMethod
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from enum import Enum

from pyfast.core.security import Authorization

import inspect
import yaml  # type: ignore


def get_field_type(field):
    return field.outer_type_


def pydantic_to_swagger(model: type[BaseModel] | dict):
    if isinstance(model, dict):
        # Handle the case when a dict is passed instead of a Pydantic model
        schema = {}
        for name, field_type in model.items():
            schema[name] = _process_field(name, field_type)
        return schema

    schema = {
        model.__name__: {
            "type": "object",
            "properties": {},
        }
    }

    for name, field in model.model_fields.items():
        schema[model.__name__]["properties"][name] = _process_field(name, field)

    return schema


def _process_field(name, field):
    if isinstance(field, FieldInfo):
        annotation = field.annotation
    else:
        annotation = field

    property_schema = {}

    if get_origin(annotation) is Union:
        args = get_args(annotation)
        if type(None) in args:
            inner_type = next(arg for arg in args if arg is not type(None))
            property_schema = _process_field(name, inner_type)
            property_schema["nullable"] = True
        else:
            property_schema["oneOf"] = [_process_field(name, arg) for arg in args]
    elif isinstance(annotation, type) and issubclass(annotation, Enum):
        property_schema["type"] = "string"
        property_schema["enum"] = [e.value for e in annotation]
    elif annotation == int:  # noqa: E721
        property_schema["type"] = "integer"
    elif annotation == float:  # noqa: E721
        property_schema["type"] = "number"
    elif annotation == str:  # noqa: E721
        property_schema["type"] = "string"
    elif annotation == bool:  # noqa: E721
        property_schema["type"] = "boolean"
    elif annotation == list or get_origin(annotation) is list:  # noqa: E721
        property_schema["type"] = "array"
        if get_args(annotation):
            item_type = get_args(annotation)[0]
            property_schema["items"] = _process_field("item", item_type)
        else:
            property_schema["items"] = {}
    elif annotation == dict or get_origin(annotation) is dict:  # noqa: E721
        property_schema["type"] = "object"
        if get_args(annotation):
            key_type, value_type = get_args(annotation)
            if key_type == str:  # noqa: E721
                property_schema["additionalProperties"] = _process_field("value", value_type)
    elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return pydantic_to_swagger(annotation)
    else:
        property_schema["type"] = "object"  # fallback for complex types

    return property_schema


class RouteSwagger:
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        name: str | None = None,
        tags: List[str] = ["Default"],
    ) -> None:
        self.path = path
        self.endpoint = endpoint
        self.tags = tags

        self.http_methods = {
            "GET": HttpMethod.GET,
            "POST": HttpMethod.POST,
            "PUT": HttpMethod.PUT,
            "DELETE": HttpMethod.DELETE,
            "PATCH": HttpMethod.PATCH,
            "HEAD": HttpMethod.HEAD,
            "OPTIONS": HttpMethod.OPTIONS,
        }

    def __call__(self, app, *args: Any, **kwds: Any) -> Any:
        router = Router()
        for name, func in self.endpoint.__dict__.items():
            if name.upper() in self.http_methods:
                _signature = inspect.signature(func)
                _summary = func.__doc__
                self.endpoint.dispatch.__doc__ = self.swagger_generate(_signature, _summary)
                endpoint_object = self.endpoint()
                dispatch = endpoint_object.dispatch
                router.add_route(
                    route_type=self.http_methods[name.upper()],
                    endpoint=self.path,
                    handler=dispatch,
                    is_const=False,
                    exception_handler=app.exception_handler,
                    injected_dependencies=app.dependencies.get_dependency_map(app),
                )

        return router

    def get_routes(self) -> List[Route]:
        return self.router.get_routes()

    def swagger_generate(self, signature: inspect.Signature, summary: str = "Document API") -> str:
        _inputs = signature.parameters.values()
        _inputs_dict = {_input.name: _input.annotation for _input in _inputs}
        _docs: Dict = {"summary": summary, "tags": self.tags, "responses": []}
        _response_type = signature.return_annotation

        for key, item in _inputs_dict.items():
            if isinstance(item, type) and issubclass(item, Authorization):
                auth_obj = item()
                _docs["security"] = [{auth_obj.name: []}]

            if isinstance(item, type) and issubclass(item, BaseModel):
                if key == "form_data":
                    _docs["requestBody"] = {"content": {"application/json": {"schema": pydantic_to_swagger(item).get(item.__name__)}}}

                if key == "query_params":
                    _docs["parameters"] = [{"name": param, "in": "query", "schema": _process_field(param, field)} for param, field in item.model_fields.items()]

                if key == "path_params":
                    path_params = [
                        {"name": param, "in": "path", "required": True, "schema": _process_field(param, field)} for param, field in item.model_fields.items()
                    ]
                    _docs.setdefault("parameters", []).extend(path_params)

        if isinstance(_response_type, type) and issubclass(_response_type, BaseModel):
            _docs["responses"] = {
                "200": {
                    "description": "Successful response",
                    # type: ignore
                    "content": {"application/json": {"schema": _response_type.model_json_schema()}},
                }
            }

        return yaml.dump(_docs)
