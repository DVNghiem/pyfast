# -*- coding: utf-8 -*-
from typing import Any, List
from robyn import Robyn
from robyn import Response
from src.core.openapi import SwaggerUI, SchemaGenerator
from src.core.route import RouteSwagger
from src.apis import routes

import ujson


class Application(Robyn):
	def __init__(self, routes: List[RouteSwagger], *args: Any, **kwargs: Any) -> None:
		super().__init__(__file__, *args, **kwargs)

		for route in routes:
			self.router.routes.extend(route(self).get_routes())


app = Application(routes=routes)


@app.get('/schema')
def schema():
	schemas = SchemaGenerator(
		{
			'openapi': '3.0.0',
			'info': {'title': 'Swagger', 'version': '1.0'},
			'servers': [{'url': '/'}],
			'components': {
				'securitySchemes': {
					'bearerAuth': {
						'type': 'http',
						'scheme': 'bearer',
						'bearerFormat': 'JWT',
					}
				}
			},
		}
	)
	return Response(
		status_code=200,
		description=ujson.dumps(schemas.get_schema(app)),
		headers={'Content-Type': 'application/json'},
	)


@app.get('/docs')
def template_render():
	swagger = SwaggerUI(
		css_url='https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css',
		js_url='https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js',
	)
	template = swagger.render_template()
	return template
