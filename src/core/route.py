# -*- coding: utf-8 -*-
from typing import Callable, Any, Dict, List, _UnionGenericAlias  # type: ignore
from robyn.router import Router, Route
from robyn import HttpMethod
from pydantic import BaseModel
from src.core.security import Authorization

import inspect
import yaml  # type: ignore


class RouteSwagger:
    def __init__(
            self,
            path: str,
            endpoint: Callable[..., Any],
            *,
            name: str | None = None,
            tags: List[str] = ['Default'],
    ) -> None:

        self.path = path
        self.endpoint = endpoint
        self.tags = tags

        self.http_methods = {
            "GET": HttpMethod.GET,
            "POST": HttpMethod.POST,
            "PUT": HttpMethod.PUT,
            "DELETE": HttpMethod.DELETE,
            "PATCH": HttpMethod.PATCH,
            "HEAD": HttpMethod.HEAD,
            "OPTIONS": HttpMethod.OPTIONS,
        }

        for name, func in self.endpoint.__dict__.items():
            if name in ['get', 'post', 'put', 'delete']:
                _signature = inspect.signature(func)
                _summary = func.__doc__
                func.__doc__ = self.swagger_generate(_signature, _summary)

    def __call__(self, app, *args: Any, **kwds: Any) -> Any:
        router = Router()
        for method in self.http_methods:
            if hasattr(self.endpoint, method.lower()):
                router.add_route(
                    route_type=self.http_methods[method],
                    endpoint=self.path,
                    handler=self.endpoint.dispatch,
                    is_const=False,
                    exception_handler=app.exception_handler,
                    injected_dependencies=app.dependencies.get_dependency_map(
                        app
                    )
                )
        return router

    def get_routes(self) -> List[Route]:
        return self.router.get_routes()

    def swagger_generate(self, signature: inspect.Signature, summary: str = 'Document API') -> str:
        _inputs = signature.parameters.values()
        _inputs_dict = {_input.name: _input.annotation for _input in _inputs}
        _docs: Dict = {'summary': summary, 'tags': self.tags, 'responses': []}
        _response_type = signature.return_annotation

        for key, item in _inputs_dict.items():
            if isinstance(item, type) and issubclass(item, Authorization):
                auth_obj = item()
                _docs['security'] = [{auth_obj.name: []}]

            if isinstance(item, type) and issubclass(item, BaseModel):
                if key == 'form_data':
                    _docs['requestBody'] = {
                        # type: ignore
                        'content': {'multipart/form-data': {'schema': item.model_json_schema()}}
                    }

                if key == 'query_params':
                    _parameters = []
                    for name, field in item.model_fields.items():  # type: ignore
                        _type = field.annotation
                        if isinstance(_type, _UnionGenericAlias):
                            _type = _type.__args__[0]
                        _parameters.append(
                            {
                                'name': name,
                                'in': 'query',
                                'required': field.is_required(),
                                'description': field.description,
                                'example': field.examples,
                                'schema': {
                                    'type': self.mapping_type.get(_type, 'string'),
                                },
                            }
                        )
                    _docs['parameters'] = _parameters

                if key == 'path_params':
                    _parameters = []
                    for name, field in item.model_fields.items():  # type: ignore
                        _type = field.annotation
                        if isinstance(_type, _UnionGenericAlias):
                            _type = _type.__args__[0]
                        _parameters.append(
                            {
                                'name': name,
                                'in': 'path',
                                'required': self.mapping_type[field.is_required()],
                                'description': field.description,
                                'example': field.examples,
                                'schema': {
                                    'type': self.mapping_type.get(_type, 'string'),
                                },
                            }
                        )
                    _docs['parameters'] = _parameters

        if isinstance(_response_type, type) and issubclass(_response_type, BaseModel):
            _docs['responses'] = {
                '200': {
                    'description': 'Successful response',
                    # type: ignore
                    'content': {'application/json': {'schema': _response_type.model_json_schema()}},
                }
            }

        return yaml.dump(_docs)

    @property
    def mapping_type(self) -> Dict:
        return {
            str: 'string',
            int: 'integer',
            True: 'true',
            False: 'false',
            float: 'float',
            bool: 'boolean',
        }
