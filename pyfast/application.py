# -*- coding: utf-8 -*-
from typing import Any, List
from robyn import Robyn
from robyn import Response, Request
from pyfast.core.openapi import SwaggerUI, SchemaGenerator
from pyfast.core.route import RouteSwagger
from pyfast.apis import routes
from pyfast.core.cache import Cache, RedisBackend, CustomKeyMaker
from pyfast.config import config

import orjson


class Application(Robyn):
    def __init__(self, routes: List[RouteSwagger], *args: Any, **kwargs: Any) -> None:
        super().__init__(__file__, *args, **kwargs)

        for route in routes:
            self.router.routes.extend(route(self).get_routes())


app = Application(routes=routes)

redis = None
if config.REDIS_URL:
    redis = RedisBackend(url=config.REDIS_URL)
    Cache.init(backend=redis, key_maker=CustomKeyMaker())


@app.get("/schema")
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
        description=orjson.dumps(schemas.get_schema(app)),
        headers={"Content-Type": "application/json"},
    )


@app.get("/docs")
def template_render():
    swagger = SwaggerUI(
        title="Swagger",
        css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
    )
    template = swagger.render_template()
    return template


# --- Global ---
@app.before_request()
def global_before_request(request: Request):
    request.headers.set("global_before", "global_before_request")
    return request


@app.after_request()
def global_after_request(response: Response):
    response.headers.set("global_after", "global_after_request")
    return response


@app.get("/sync/global/middlewares")
def sync_global_middlewares(request: Request):
    print(request.headers)
    print(request.headers.get("txt"))
    print(request.headers["txt"])
    assert "global_before" in request.headers
    assert request.headers.get("global_before") == "global_before_request"
    return "sync global middlewares"


@app.before_request("/sync/middlewares")
def sync_before_request(request: Request):
    request.headers.set("before", "sync_before_request")
    return request


@app.after_request("/sync/middlewares")
def sync_after_request(response: Response):
    response.headers.set("after", "sync_after_request")
    response.description = response.description + " after"
    return response


if __name__ == "__main__":
    app.start()
