from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

@dataclass
class BaseBackend:
    get: Callable[[str], Any]
    set: Callable[[Any, str, int], None]
    delete_startswith: Callable[[str], None]

@dataclass
class RedisBackend(BaseBackend):
    url: str

    get: Callable[[str], Any]
    set: Callable[[Any, str, int], None]
    delete_startswith: Callable[[str], None]

@dataclass
class BaseSchemaGenerator:
    remove_converter: Callable[[str], str]
    parse_docstring: Callable[[Callable[..., Any]], str]

@dataclass
class SwaggerUI:
    title: str
    openapi_url: str

    render_template: Callable[..., Any]
    get_html_content: Callable[..., str]
