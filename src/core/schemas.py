# -*- coding: utf-8 -*-
from starlette.schemas import BaseSchemaGenerator
from starlette.routing import BaseRoute
import typing


class SchemaGenerator(BaseSchemaGenerator):
	def __init__(self, base_schema: dict[str, typing.Any]) -> None:
		self.base_schema = base_schema

	def parse_docstring(
		self, func_or_method: typing.Callable[..., typing.Any]
	) -> dict[str, typing.Any]:
		try:
			return super().parse_docstring(func_or_method)
		except Exception:
			return {}

	def get_schema(self, routes: list[BaseRoute]) -> dict[str, typing.Any]:
		schema = dict(self.base_schema)
		schema.setdefault('paths', {})
		endpoints_info = self.get_endpoints(routes)

		for endpoint in endpoints_info:
			parsed = self.parse_docstring(endpoint.func)

			if not parsed:
				continue

			if endpoint.path not in schema['paths']:
				schema['paths'][endpoint.path] = {}

			schema['paths'][endpoint.path][endpoint.http_method] = parsed

		return schema
