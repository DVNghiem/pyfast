# -*- coding: utf-8 -*-
from typing import Any, List

from robyn import Robyn
from robyn import Response

import orjson

from pyfast.openapi import SwaggerUI, SchemaGenerator
from pyfast.routing import Route
from pyfast.logging import reset_logger

reset_logger()


class Application(Robyn):
    def __init__(self, routes: List[Route] = [], *args: Any, **kwargs: Any) -> None:
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

    def add_middleware(self, middleware):
        setattr(middleware, "app", self)
        before_request = getattr(middleware, "before_request", None)
        after_request = getattr(middleware, "after_request", None)
        endpoint = getattr(middleware, "endpoint", None)
        if before_request:
            self.before_request(endpoint=endpoint)(before_request)
        if after_request:
            self.after_request(endpoint=endpoint)(after_request)
        return self
