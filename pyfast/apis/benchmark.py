from robyn import Request, jsonify, Response
from pyfast.core.endpoint import HTTPEndpoint
from pyfast.core.route import RouteSwagger
from pydantic import BaseModel

__base_route__ = "/benchmark"


class RequestFile(HTTPEndpoint):
    def post(self, request: Request):
        files = request.files
        file_names = files.keys()  # noqa
        return Response(
            status_code=200,
            description="multipart form data",
            headers={"Content-Type": "application/json"},
        )


class SyncQuery(HTTPEndpoint):
    def get(self, request: Request):
        return jsonify({"message": "Hello World!"})


class AsyncQuery(HTTPEndpoint):
    async def get(self, request: Request):
        return jsonify({"message": "Hello World!"})


class ResponseObject(HTTPEndpoint):
    def get(self, request: Request):
        return Response(
            status_code=200,
            description={"message": "Hello World!"},
            headers={"Content-Type": "application/json"},
        )


# ======= validate BaseModel =======
class ModelRequest(BaseModel):
    name: str
    age: int


class ModelResponse(BaseModel):
    message: str


class ValidateModel(HTTPEndpoint):
    def post(self, request: Request, form_data: ModelRequest) -> ModelResponse:
        return ModelResponse(message=f"Hello {form_data.name}! You are {form_data.age} years old.")

    async def get(self) -> ModelResponse:
        return {"message": "Hello World!"}


routes = [
    RouteSwagger(f"{__base_route__}/file", RequestFile),
    RouteSwagger(f"{__base_route__}/sync", SyncQuery),
    RouteSwagger(f"{__base_route__}/async", AsyncQuery),
    RouteSwagger(f"{__base_route__}/response", ResponseObject),
    RouteSwagger(f"{__base_route__}/validate", ValidateModel),
]
