# -*- coding: utf-8 -*-
from pyfast import Application, Request, Response, jsonify
from pyfast.routing import HTTPEndpoint, Router
from pydantic import BaseModel

__base_route__ = "/benchmark"

MESSAGE = "Hello World!"


class RequestFile(HTTPEndpoint):
    def post(self, request: Request):
        print(request)
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


routes = [
    Router(f"{__base_route__}/file", RequestFile),
    Router(f"{__base_route__}/sync", SyncQuery),
    Router(f"{__base_route__}/async", AsyncQuery),
    Router(f"{__base_route__}/response", ResponseObject),
    Router(f"{__base_route__}/validate", ValidateModel),
]

app = Application(routes=routes)

redis = None


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
    app.start(port=5005)
