# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import socket
from typing import Any, Callable, List, TypeVar

import orjson
from typing_extensions import Annotated, Doc

from hypern.datastructures import Contact, HTTPMethod, Info, License
from hypern.exceptions import InvalidPortNumber
from hypern.hypern import FunctionInfo, Router
from hypern.hypern import Route as InternalRoute
from hypern.logging import logger, reset_logger
from hypern.openapi import SchemaGenerator, SwaggerUI
from hypern.processpool import run_processes
from hypern.response import HTMLResponse, JSONResponse
from hypern.routing import Route
from hypern.scheduler import Scheduler
from hypern.middleware import Middleware

reset_logger()

AppType = TypeVar("AppType", bound="Hypern")


class Hypern:
    def __init__(
        self: AppType,
        routes: Annotated[
            List[Route] | None,
            Doc(
                """
                A list of routes to serve incoming HTTP and WebSocket requests.
                You can define routes using the `Route` class from `Hypern.routing`.
                **Example**
                ---
                ```python
                class DefaultRoute(HTTPEndpoint):
                    async def get(self, global_dependencies):
                        return PlainTextResponse("/hello")
                Route("/test", DefaultRoute)

                # Or you can define routes using the decorator
                route = Route("/test)
                @route.get("/route")
                def def_get():
                    return PlainTextResponse("Hello")
                ```
                """
            ),
        ] = None,
        title: Annotated[
            str,
            Doc(
                """
                The title of the API.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more in the
                """
            ),
        ] = "Hypern",
        summary: Annotated[
            str | None,
            Doc(
                """"
                A short summary of the API.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        description: Annotated[
            str,
            Doc(
                """
                A description of the API. Supports Markdown (using
                [CommonMark syntax](https://commonmark.org/)).

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = "",
        version: Annotated[
            str,
            Doc(
                """
                The version of the API.

                **Note** This is the version of your application, not the version of
                the OpenAPI specification nor the version of Application being used.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = "0.0.1",
        contact: Annotated[
            Contact | None,
            Doc(
                """
                A dictionary with the contact information for the exposed API.

                It can contain several fields.

                * `name`: (`str`) The name of the contact person/organization.
                * `url`: (`str`) A URL pointing to the contact information. MUST be in
                    the format of a URL.
                * `email`: (`str`) The email address of the contact person/organization.
                    MUST be in the format of an email address.            
                """
            ),
        ] = None,
        openapi_url: Annotated[
            str | None,
            Doc(
                """
                The URL where the OpenAPI schema will be served from.

                If you set it to `None`, no OpenAPI schema will be served publicly, and
                the default automatic endpoints `/docs` and `/redoc` will also be
                disabled.
            """
            ),
        ] = "/openapi.json",
        docs_url: Annotated[
            str | None,
            Doc(
                """
                The path to the automatic interactive API documentation.
                It is handled in the browser by Swagger UI.

                The default URL is `/docs`. You can disable it by setting it to `None`.

                If `openapi_url` is set to `None`, this will be automatically disabled.
            """
            ),
        ] = "/docs",
        license_info: Annotated[
            License | None,
            Doc(
                """
                A dictionary with the license information for the exposed API.

                It can contain several fields.

                * `name`: (`str`) **REQUIRED** (if a `license_info` is set). The
                    license name used for the API.
                * `identifier`: (`str`) An [SPDX](https://spdx.dev/) license expression
                    for the API. The `identifier` field is mutually exclusive of the `url`
                    field. Available since OpenAPI 3.1.0
                * `url`: (`str`) A URL to the license used for the API. This MUST be
                    the format of a URL.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                **Example**

                ```python
                app = Hypern(
                    license_info={
                        "name": "Apache 2.0",
                        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
                    }
                )
                ```
                """
            ),
        ] = None,
        scheduler: Annotated[
            Scheduler | None,
            Doc(
                """
                A scheduler to run background tasks.
                """
            ),
        ] = None,
        default_injectables: Annotated[
            dict[str, Any] | None,
            Doc(
                """
                A dictionary of default injectables to be passed to all routes.
                """
            ),
        ] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.router = Router(path="/")
        self.scheduler = scheduler
        self.injectables = default_injectables or {}
        self.middleware_before_request = []
        self.middleware_after_request = []

        for route in routes:
            self.router.extend_route(route(app=self).routes)

        if openapi_url and docs_url:
            self.add_openapi(
                info=Info(
                    title=title,
                    summary=summary,
                    description=description,
                    version=version,
                    contact=contact,
                    license=license_info,
                ),
                openapi_url=openapi_url,
                docs_url=docs_url,
            )

    def add_openapi(
        self,
        info: Info,
        openapi_url: str,
        docs_url: str,
    ):
        def schema(*args, **kwargs):
            schemas = SchemaGenerator(
                {
                    "openapi": "3.0.0",
                    "info": info.model_dump(),
                    "components": {"securitySchemes": {}},
                }
            )
            return JSONResponse(content=orjson.dumps(schemas.get_schema(self)))

        def template_render(*args, **kwargs):
            swagger = SwaggerUI(
                title="Swagger",
                openapi_url=openapi_url,
            )
            template = swagger.get_html_content()
            return HTMLResponse(template)

        self.add_route(HTTPMethod.GET, openapi_url, schema)
        self.add_route(HTTPMethod.GET, docs_url, template_render)

    def before_request(self):
        def decorator(func):
            is_async = asyncio.iscoroutinefunction(func)
            func_info = FunctionInfo(handler=func, is_async=is_async)
            self.middleware_before_request.append(func_info)
            return func

        return decorator

    def after_request(self):
        def decorator(func):
            is_async = asyncio.iscoroutinefunction(func)
            func_info = FunctionInfo(handler=func, is_async=is_async)
            self.middleware_after_request.append(func_info)
            return func

        return decorator

    def inject(self, key: str, value: Any):
        self.injectables[key] = value
        return self

    def add_middleware(self, middleware: Middleware):
        setattr(middleware, "app", self)
        before_request = getattr(middleware, "before_request", None)
        after_request = getattr(middleware, "after_request", None)

        if before_request:
            self.before_request()(before_request)
        if after_request:
            self.after_request()(after_request)
        return self

    def is_port_in_use(self, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", port)) == 0
        except Exception:
            raise InvalidPortNumber(f"Invalid port number: {port}")

    def start(self, host: str = "127.0.0.1", port: int = 8080, workers=1, processes=1, check_port=False):
        if check_port:
            while self.is_port_in_use(port):
                logger.error("Port %s is already in use. Please use a different port.", port)
                try:
                    port = int(input("Enter a different port: "))
                except Exception:
                    logger.error("Invalid port number. Please enter a valid port number.")
                    continue

        if self.scheduler:
            self.scheduler.start()

        run_processes(
            host=host,
            port=port,
            workers=workers,
            processes=processes,
            router=self.router,
            injectables=self.injectables,
            before_request=self.middleware_before_request,
            after_request=self.middleware_after_request,
        )

    def add_route(self, method: HTTPMethod, endpoint: str, handler: Callable[..., Any]):
        is_async = asyncio.iscoroutinefunction(handler)
        func_info = FunctionInfo(handler=handler, is_async=is_async)
        route = InternalRoute(path=endpoint, function=func_info, method=method.name)
        self.router.add_route(route=route)
