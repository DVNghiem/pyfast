# -*- coding: utf-8 -*-
from hypern import Hypern, Request, Response, jsonify
from hypern.routing import HTTPEndpoint, Route
from hypern.response import JSONResponse, HTMLResponse, PlainTextResponse, RedirectResponse, FileResponse

from pydantic import BaseModel

__base_route__ = "/benchmark"

MESSAGE = "Hello World!"


class DefaultRoute(HTTPEndpoint):
    def post(self, request: Request):
        return JSONResponse({"message": MESSAGE})


class RequestFile(HTTPEndpoint):
    def post(self, request: Request):
        print(request.files)
        return Response(
            status_code=200,
            description="multipart form data",
            headers={"Content-Type": "application/json"},
        )


class SyncQuery(HTTPEndpoint):
    def get(self, request: Request):
        return jsonify({"message": MESSAGE})


class AsyncQuery(HTTPEndpoint):
    async def get(self, request: Request):
        return jsonify({"message": MESSAGE})


class ResponseObject(HTTPEndpoint):
    def get(self, request: Request):
        return Response(
            status_code=200,
            description={"message": MESSAGE},
            headers={"Content-Type": "application/json"},
        )


class ModelRequest(BaseModel):
    name: str
    age: int


class ModelResponse(BaseModel):
    message: str


class ValidateModel(HTTPEndpoint):
    def post(self, request: Request, form_data: ModelRequest) -> ModelResponse:
        return ModelResponse(message=f"Hello {form_data.name}! You are {form_data.age} years old.")

    async def get(self) -> ModelResponse:
        return ModelResponse(message=MESSAGE)


# response type
class TestJsonResponse(HTTPEndpoint):
    def post(self, request: Request):
        return JSONResponse({"message": MESSAGE})


class TestHtmlResponse(HTTPEndpoint):
    def post(self, request: Request):
        return HTMLResponse("<h1>Hello World!</h1>")


class TestPlainTextResponse(HTTPEndpoint):
    def post(self, request: Request):
        return PlainTextResponse("Hello World!")


class TestRedirectResponse(HTTPEndpoint):
    def post(self, request: Request):
        return RedirectResponse("/benchmark/default")


class TestFileResponse(HTTPEndpoint):
    def get(self, request: Request):
        return FileResponse(b"Hello", "hello.txt")


functional_route = Route("/functional")


@functional_route.get("/default")
def get(request: Request, query_params: ModelRequest):
    return jsonify({"message": MESSAGE})


@functional_route.post("/default")
def post(request: Request, global_dependencies):
    return jsonify({"message": MESSAGE})


@functional_route.put("/default")
def put(request: Request, router_dependencies):
    return jsonify({"message": MESSAGE})


@functional_route.delete("/default")
def delete(request: Request):
    return jsonify({"message": MESSAGE})


routes = [
    Route(f"{__base_route__}/default", DefaultRoute),
    Route(f"{__base_route__}/file", RequestFile),
    Route(f"{__base_route__}/sync", SyncQuery),
    Route(f"{__base_route__}/async", AsyncQuery),
    Route(f"{__base_route__}/response", ResponseObject),
    Route(f"{__base_route__}/validate", ValidateModel),
    Route(f"{__base_route__}/json", TestJsonResponse),
    Route(f"{__base_route__}/html", TestHtmlResponse),
    Route(f"{__base_route__}/plain_text", TestPlainTextResponse),
    Route(f"{__base_route__}/redirect", TestRedirectResponse),
    Route(f"{__base_route__}/file", TestFileResponse),
    functional_route,
]

app = Hypern(routes=routes)


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
    app.start(port=5005)
