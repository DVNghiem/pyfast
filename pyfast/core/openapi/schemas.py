# -*- coding: utf-8 -*-
from robyn.router import Route
from robyn import Robyn, HttpMethod
import typing
import yaml
import re


class EndpointInfo(typing.NamedTuple):
    path: str
    http_method: str
    func: typing.Callable[..., typing.Any]


class BaseSchemaGenerator:
    def get_schema(self, routes: list[Route]) -> dict[str, typing.Any]:
        raise NotImplementedError()  # pragma: no cover

    def get_endpoints(self, routes: list[Route]) -> list[EndpointInfo]:
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
            method = route.route_type
            http_method = "get"
            if method == HttpMethod.POST:
                http_method = "post"
            elif method == HttpMethod.PUT:
                http_method = "put"
            elif method == HttpMethod.PATCH:
                http_method = "patch"
            elif method == HttpMethod.DELETE:
                http_method = "delete"
            elif method == HttpMethod.OPTIONS:
                http_method = "options"
            endpoints_info.append(EndpointInfo(path=route.route, http_method=http_method, func=route.function.handler))

        return endpoints_info

    def _remove_converter(self, path: str) -> str:
        """
        Remove the converter from the path.
        For example, a route like this:
            Route("/users/{id:int}", endpoint=get_user, methods=["GET"])
        Should be represented as `/users/{id}` in the OpenAPI schema.
        """
        return re.sub(r":\w+}", "}", path)

    def parse_docstring(self, func_or_method: typing.Callable[..., typing.Any]) -> dict[str, typing.Any]:
        """
        Given a function, parse the docstring as YAML and return a dictionary of info.
        """
        docstring = func_or_method.__doc__
        if not docstring:
            return {}

        assert yaml is not None, "`pyyaml` must be installed to use parse_docstring."

        # We support having regular docstrings before the schema
        # definition. Here we return just the schema part from
        # the docstring.
        docstring = docstring.split("---")[-1]

        parsed = yaml.safe_load(docstring)

        if not isinstance(parsed, dict):
            # A regular docstring (not yaml formatted) can return
            # a simple string here, which wouldn't follow the schema.
            return {}

        return parsed


class SchemaGenerator(BaseSchemaGenerator):
    def __init__(self, base_schema: dict[str, typing.Any]) -> None:
        super().__init__()
        self.base_schema = base_schema

    def parse_docstring(self, func_or_method: typing.Callable[..., typing.Any]) -> dict[str, typing.Any]:
        try:
            return super().parse_docstring(func_or_method)
        except Exception:
            return {}

    def get_schema(self, app: Robyn) -> dict[str, typing.Any]:
        schema = dict(self.base_schema)
        schema.setdefault("paths", {})
        endpoints_info = self.get_endpoints(app.router.get_routes())

        for endpoint in endpoints_info:
            parsed = self.parse_docstring(endpoint.func)

            if not parsed:
                continue

            if endpoint.path not in schema["paths"]:
                schema["paths"][endpoint.path] = {}

            schema["paths"][endpoint.path][endpoint.http_method] = parsed

        return schema
