# -*- coding: utf-8 -*-
from typing import Callable, Any, Dict, List, Union, Type, get_origin, get_args
from robyn.router import Router as RobynRouter
from robyn import HttpMethod, Request
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from enum import Enum

import inspect
import yaml  # type: ignore

from pyfast.auth.authorization import Authorization
from .dispatcher import dispatch


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


class SchemaProcessor:
    @staticmethod
    def process_union(args: tuple) -> Dict[str, Any]:
        """Process Union types"""
        if type(None) in args:
            inner_type = next(arg for arg in args if arg is not type(None))
            schema = SchemaProcessor._process_field("", inner_type)
            schema["nullable"] = True
            return schema
        return {"oneOf": [SchemaProcessor._process_field("", arg) for arg in args]}

    @staticmethod
    def process_enum(annotation: Type[Enum]) -> Dict[str, Any]:
        """Process Enum types"""
        return {"type": "string", "enum": [e.value for e in annotation]}

    @staticmethod
    def process_primitive(annotation: type) -> Dict[str, str]:
        """Process primitive types"""
        type_mapping = {int: "integer", float: "number", str: "string", bool: "boolean"}
        return {"type": type_mapping.get(annotation, "object")}

    @staticmethod
    def process_list(annotation: type) -> Dict[str, Any]:
        """Process list types"""
        schema = {"type": "array"}

        args = get_args(annotation)
        if args:
            item_type = args[0]
            schema["items"] = SchemaProcessor._process_field("item", item_type)
        else:
            schema["items"] = {}
        return schema

    @staticmethod
    def process_dict(annotation: type) -> Dict[str, Any]:
        """Process dict types"""
        schema = {"type": "object"}

        args = get_args(annotation)
        if args:
            key_type, value_type = args
            if key_type == str:  # noqa: E721
                schema["additionalProperties"] = SchemaProcessor._process_field("value", value_type)
        return schema

    @classmethod
    def _process_field(cls, name: str, field: Any) -> Dict[str, Any]:
        """Process a single field"""
        if isinstance(field, FieldInfo):
            annotation = field.annotation
        else:
            annotation = field

        # Process Union types
        origin = get_origin(annotation)
        if origin is Union:
            return cls.process_union(get_args(annotation))

        # Process Enum types
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return cls.process_enum(annotation)

        # Process primitive types
        if annotation in {int, float, str, bool}:
            return cls.process_primitive(annotation)

        # Process list types
        if annotation == list or origin is list:  # noqa: E721
            return cls.process_list(annotation)

        # Process dict types
        if annotation == dict or origin is dict:  # noqa: E721
            return cls.process_dict(annotation)

        # Process Pydantic models
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return pydantic_to_swagger(annotation)

        # Fallback for complex types
        return {"type": "object"}


def _process_field(name: str, field: Any) -> Dict[str, Any]:
    """
    Process a field and return its schema representation

    Args:
        name: Field name
        field: Field type or FieldInfo object

    Returns:
        Dictionary representing the JSON schema for the field
    """
    return SchemaProcessor._process_field(name, field)


class Route:
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        tags: List[str] | None = None,
    ) -> None:
        self.path = path
        self.endpoint = endpoint
        self.tags = tags or ["Default"]
        self.name = name

        self.http_methods = {
            "GET": HttpMethod.GET,
            "POST": HttpMethod.POST,
            "PUT": HttpMethod.PUT,
            "DELETE": HttpMethod.DELETE,
            "PATCH": HttpMethod.PATCH,
            "HEAD": HttpMethod.HEAD,
            "OPTIONS": HttpMethod.OPTIONS,
        }
        self.functional_handlers = []

    def swagger_generate(self, signature: inspect.Signature, summary: str = "Document API") -> str:
        _inputs = signature.parameters.values()
        _inputs_dict = {_input.name: _input.annotation for _input in _inputs}
        _docs: Dict = {"summary": summary, "tags": self.tags, "responses": [], "name": self.name}
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

    def _combine_path(self, path1: str, path2: str) -> str:
        if path1.endswith("/") and path2.startswith("/"):
            return path1 + path2[1:]
        if not path1.endswith("/") and not path2.startswith("/"):
            return path1 + "/" + path2
        return path1 + path2

    def __call__(self, app, *args: Any, **kwds: Any) -> Any:
        router = RobynRouter()

        # Validate handlers
        if not self.endpoint and not self.functional_handlers:
            raise ValueError(f"No handler found for route: {self.path}")

        default_params = {"is_const": False, "injected_dependencies": app.dependencies.get_dependency_map(app), "exception_handler": app.exception_handler}

        # Handle functional routes
        for h in self.functional_handlers:
            router.add_route(
                route_type=self.http_methods[h["method"].upper()], endpoint=self._combine_path(self.path, h["path"]), handler=h["func"], **default_params
            )

        if not self.endpoint:
            return router

        # Handle class-based routes
        for name, func in self.endpoint.__dict__.items():
            if name.upper() in self.http_methods:
                sig = inspect.signature(func)
                doc = self.swagger_generate(sig, func.__doc__)
                self.endpoint.dispatch.__doc__ = doc
                endpoint_obj = self.endpoint()
                router.add_route(route_type=self.http_methods[name.upper()], endpoint=self.path, handler=endpoint_obj.dispatch, **default_params)
                del endpoint_obj  # free up memory

        return router

    def route(
        self,
        path: str,
        method: str,
        *args: Any,
        **kwds: Any,
    ) -> Callable:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            async def functional_wrapper(request: Request, global_dependencies, router_dependencies) -> Any:
                return await dispatch(func, request, global_dependencies, router_dependencies)

            sig = inspect.signature(func)
            functional_wrapper.__doc__ = self.swagger_generate(sig, func.__doc__)

            self.functional_handlers.append(
                {
                    "path": path,
                    "method": method,
                    "func": functional_wrapper,
                }
            )

        return decorator

    def get(self, path: str) -> Callable:
        return self.route(path, "GET")

    def post(self, path: str) -> Callable:
        return self.route(path, "POST")

    def put(self, path: str) -> Callable:
        return self.route(path, "PUT")

    def delete(self, path: str) -> Callable:
        return self.route(path, "DELETE")

    def patch(self, path: str) -> Callable:
        return self.route(path, "PATCH")

    def head(self, path: str) -> Callable:
        return self.route(path, "HEAD")

    def options(self, path: str) -> Callable:
        return self.route(path, "OPTIONS")
