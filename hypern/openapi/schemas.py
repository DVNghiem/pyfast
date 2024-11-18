# -*- coding: utf-8 -*-
from __future__ import annotations

from hypern.hypern import BaseSchemaGenerator, Route as InternalRoute
import typing
import orjson


class EndpointInfo(typing.NamedTuple):
    path: str
    http_method: str
    func: typing.Callable[..., typing.Any]


class SchemaGenerator(BaseSchemaGenerator):
    def __init__(self, base_schema: dict[str, typing.Any]) -> None:
        self.base_schema = base_schema

    def get_endpoints(self, routes: list[InternalRoute]) -> list[EndpointInfo]:
        """
        Given the routes, yields the following information:

        - path
            eg: /users/
        - http_method
            one of 'get', 'post', 'put', 'patch', 'delete', 'options'
        - func
            method ready to extract the docstring
        """
        endpoints_info: list[EndpointInfo] = []

        for route in routes:
            method = route.method.lower()
            endpoints_info.append(EndpointInfo(path=route.path, http_method=method, func=route.function.handler))
        return endpoints_info

    def get_schema(self, app) -> dict[str, typing.Any]:
        schema = dict(self.base_schema)
        schema.setdefault("paths", {})
        endpoints_info = self.get_endpoints(app.router.routes)

        for endpoint in endpoints_info:
            parsed = self.parse_docstring(endpoint.func)

            if not parsed:
                continue

            if endpoint.path not in schema["paths"]:
                schema["paths"][endpoint.path] = {}

            schema["paths"][endpoint.path][endpoint.http_method] = orjson.loads(parsed)

        return schema
