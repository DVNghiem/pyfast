# -*- coding: utf-8 -*-
from typing import Any, List

from robyn import Robyn
from robyn import Response

import orjson

from pyfast.openapi import SwaggerUI, SchemaGenerator
from pyfast.routing import Router
from pyfast.logging import reset_logger

reset_logger()


class Application(Robyn):
    def __init__(self, routes: List[Router] = [], *args: Any, **kwargs: Any) -> None:
        super().__init__(__file__, *args, **kwargs)

        for route in routes:
            self.router.routes.extend(route(self).get_routes())

        @self.get("/schema")
        def schema():
            schemas = SchemaGenerator(
                {
                    "openapi": "3.0.0",
                    "info": {"title": "Swagger", "version": "1.0"},
                    "servers": [{"url": "/"}],
                    "components": {
                        "securitySchemes": {
                            "bearerAuth": {
                                "type": "http",
                                "scheme": "bearer",
                                "bearerFormat": "JWT",
                            }
                        }
                    },
                }
            )
            return Response(
                status_code=200,
                description=orjson.dumps(schemas.get_schema(self)),
                headers={"Content-Type": "application/json"},
            )

        @self.get("/docs")
        def template_render():
            swagger = SwaggerUI(
                title="Swagger",
                css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
                js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
            )
            template = swagger.render_template()
            return template
