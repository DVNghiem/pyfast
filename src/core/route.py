from typing import Callable, Any, Dict, List, _UnionGenericAlias
from starlette.routing import Route
from pydantic import BaseModel
from src.core.security import Authorization

import inspect
import yaml

# _UnionGenericAlias = dict


class RouteSwagger(Route):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: List[str] | None = None,
        name: str | None = None,
        include_in_schema: bool = True,
        tags: List[str] = ["Default"],
    ) -> None:
        super().__init__(
            path,
            endpoint,
            methods=methods,
            name=name,
            include_in_schema=include_in_schema,
        )
        self.tags = tags
        for name, func in endpoint.__dict__.items():
            if name in ["get", "post", "put", "delete"]:
                _signature = inspect.signature(func)
                _summary = func.__doc__
                func.__doc__ = self.swagger_generate(_signature, _summary)

    def swagger_generate(
        self, signature: inspect.Signature, summary: str = "Document API"
    ) -> str:
        _inputs = signature.parameters.values()
        _inputs_dict = {_input.name: _input.annotation for _input in _inputs}
        _docs: Dict = {"summary": summary, "tags": self.tags, "responses": []}
        _response_type = signature.return_annotation

        for key, item in _inputs_dict.items():
            if isinstance(item, type) and issubclass(item, Authorization):
                auth_obj = item()
                _docs["security"] = [{auth_obj.name: []}]

            if isinstance(item, type) and issubclass(item, BaseModel):
                if key == "form_data":
                    _docs["requestBody"] = {
                        "content": {
                            "multipart/form-data": {"schema": item.model_json_schema()}
                        }
                    }

                if key == "query_params":
                    _parameters = []
                    for name, field in item.model_fields.items():
                        _type = field.annotation
                        if isinstance(_type, _UnionGenericAlias):
                            _type = _type.__args__[0]
                        _parameters.append(
                            {
                                "name": name,
                                "in": "query",
                                "required": field.is_required(),
                                "description": field.description,
                                "example": field.examples,
                                "schema": {
                                    "type": self.mapping_type.get(_type, "string"),
                                },
                            }
                        )
                    _docs["parameters"] = _parameters

                if key == "path_params":
                    _parameters = []
                    for name, field in item.model_fields.items():
                        _type = field.annotation
                        if isinstance(_type, _UnionGenericAlias):
                            _type = _type.__args__[0]
                        _parameters.append(
                            {
                                "name": name,
                                "in": "path",
                                "required": self.mapping_type[field.is_required()],
                                "description": field.description,
                                "example": field.examples,
                                "schema": {
                                    "type": self.mapping_type.get(_type, "string"),
                                },
                            }
                        )
                    _docs["parameters"] = _parameters

        if isinstance(_response_type, type) and issubclass(_response_type, BaseModel):
            _docs["responses"] = {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": _response_type.model_json_schema()
                        }
                    },
                }
            }

        return yaml.dump(_docs)

    @property
    def mapping_type(self) -> Dict:
        return {
            str: "string",
            int: "integer",
            True: "true",
            False: "false",
            float: "float",
            bool: "boolean",
        }
