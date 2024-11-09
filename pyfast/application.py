# -*- coding: utf-8 -*-
from typing import Any, List, TypeVar
from typing_extensions import Annotated, Doc
from robyn import Robyn
import orjson

from pyfast.openapi import SwaggerUI, SchemaGenerator
from pyfast.routing import Route
from pyfast.response import JSONResponse
from pyfast.logging import reset_logger
from pyfast.datastructures import Contact, License, Info

reset_logger()

AppType = TypeVar("AppType", bound="PyFast")


class PyFast(Robyn):
    def __init__(
        self: AppType,
        routes: Annotated[
            List[Route] | None,
            Doc(
                """
                A list of routes to serve incoming HTTP and WebSocket requests.
                You can define routes using the `Route` class from `pyfast.routing`.
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
        ] = "PyFast",
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
                app = PyFast(
                    license_info={
                        "name": "Apache 2.0",
                        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
                    }
                )
                ```
                """
            ),
        ] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(__file__, *args, **kwargs)

        for route in routes:
            self.router.routes.extend(route(self).get_routes())

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
        @self.get(openapi_url)
        def schema():
            schemas = SchemaGenerator(
                {
                    "openapi": "3.0.0",
                    "info": info.model_dump(),
                    "components": {"securitySchemes": {}},
                }
            )
            return JSONResponse(content=orjson.dumps(schemas.get_schema(self)))

        @self.get(docs_url)
        def template_render():
            swagger = SwaggerUI(
                title="Swagger",
                openapi_url=openapi_url,
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
