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
from hypern.logging import logger
from hypern.openapi import SchemaGenerator, SwaggerUI
from hypern.processpool import run_processes
from hypern.response import HTMLResponse, JSONResponse
from hypern.routing import Route
from hypern.scheduler import Scheduler
from hypern.middleware import Middleware

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
        self.response_headers = {}

        for route in routes:
            self.router.extend_route(route(app=self).routes)

        if openapi_url and docs_url:
            self.__add_openapi(
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

    def __add_openapi(
        self,
        info: Info,
        openapi_url: str,
        docs_url: str,
    ):
        """
        Adds OpenAPI schema and documentation routes to the application.

        Args:
            info (Info): An instance of the Info class containing metadata about the API.
            openapi_url (str): The URL path where the OpenAPI schema will be served.
            docs_url (str): The URL path where the Swagger UI documentation will be served.

        The method defines two internal functions:
            - schema: Generates and returns the OpenAPI schema as a JSON response.
            - template_render: Renders and returns the Swagger UI documentation as an HTML response.

        The method then adds routes to the application for serving the OpenAPI schema and the Swagger UI documentation.
        """

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

    def add_response_header(self, key: str, value: str):
        """
        Adds a response header to the response headers dictionary.

        Args:
            key (str): The header field name.
            value (str): The header field value.
        """
        self.response_headers[key] = value

    def before_request(self):
        """
        A decorator to register a function to be executed before each request.

        This decorator can be used to add middleware functions that will be
        executed before the main request handler. The function can be either
        synchronous or asynchronous.

        Returns:
            function: The decorator function that registers the middleware.
        """

        def decorator(func):
            is_async = asyncio.iscoroutinefunction(func)
            func_info = FunctionInfo(handler=func, is_async=is_async)
            self.middleware_before_request.append(func_info)
            return func

        return decorator

    def after_request(self):
        """
        Decorator to register a function to be called after each request.

        This decorator can be used to register both synchronous and asynchronous functions.
        The registered function will be wrapped in a FunctionInfo object and appended to the
        middleware_after_request list.

        Returns:
            function: The decorator function that registers the given function.
        """

        def decorator(func):
            is_async = asyncio.iscoroutinefunction(func)
            func_info = FunctionInfo(handler=func, is_async=is_async)
            self.middleware_after_request.append(func_info)
            return func

        return decorator

    def inject(self, key: str, value: Any):
        """
        Injects a key-value pair into the injectables dictionary.

        Args:
            key (str): The key to be added to the injectables dictionary.
            value (Any): The value to be associated with the key.

        Returns:
            self: Returns the instance of the class to allow method chaining.
        """
        self.injectables[key] = value
        return self

    def add_middleware(self, middleware: Middleware):
        """
        Adds middleware to the application.

        This method attaches the middleware to the application instance and registers
        its `before_request` and `after_request` hooks if they are defined.

        Args:
            middleware (Middleware): The middleware instance to be added.

        Returns:
            self: The application instance with the middleware added.
        """
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

    def start(
        self,
        host: Annotated[str, Doc("The host to run the server on. Defaults to `127.0.0.1`")] = "127.0.0.1",
        port: Annotated[int, Doc("The port to run the server on. Defaults to `8080`")] = 8080,
        workers: Annotated[int, Doc("The number of workers to run. Defaults to `1`")] = 1,
        processes: Annotated[int, Doc("The number of processes to run. Defaults to `1`")] = 1,
        max_blocking_threads: Annotated[int, Doc("The maximum number of blocking threads. Defaults to `100`")] = 1,
        check_port: Annotated[bool, Doc("Check if the port is already in use. Defaults to `True`")] = False,
    ):
        """
        Starts the server with the specified configuration.

        Args:
            host (str): The host to run the server on. Defaults to `127.0.0.1`.
            port (int): The port to run the server on. Defaults to `8080`.
            workers (int): The number of workers to run. Defaults to `1`.
            processes (int): The number of processes to run. Defaults to `1`.
            max_blocking_threads (int): The maximum number of blocking threads. Defaults to `100`.
            check_port (bool): Check if the port is already in use. Defaults to `True`.

        Raises:
            ValueError: If an invalid port number is entered when prompted.

        """
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
            max_blocking_threads=max_blocking_threads,
            router=self.router,
            injectables=self.injectables,
            before_request=self.middleware_before_request,
            after_request=self.middleware_after_request,
            response_headers=self.response_headers,
        )

    def add_route(self, method: HTTPMethod, endpoint: str, handler: Callable[..., Any]):
        """
        Adds a route to the router.

        Args:
            method (HTTPMethod): The HTTP method for the route (e.g., GET, POST).
            endpoint (str): The endpoint path for the route.
            handler (Callable[..., Any]): The function that handles requests to the route.

        """
        is_async = asyncio.iscoroutinefunction(handler)
        func_info = FunctionInfo(handler=handler, is_async=is_async)
        route = InternalRoute(path=endpoint, function=func_info, method=method.name)
        self.router.add_route(route=route)
