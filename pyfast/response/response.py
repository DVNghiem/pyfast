from __future__ import annotations

import typing
from urllib.parse import quote
from robyn import Response as RobynResponse, Headers


class Response:
    media_type = None
    charset = "utf-8"

    def __init__(
        self,
        content: typing.Any = None,
        status_code: int = 200,
        headers: typing.Mapping[str, str] | None = None,
        media_type: str | None = None,
    ) -> None:
        self.status_code = status_code
        if media_type is not None:
            self.media_type = media_type
        self.body = self.render(content)
        self.init_headers(headers)

    def render(self, content: typing.Any) -> bytes | memoryview:
        if content is None:
            return b""
        if isinstance(content, (bytes, memoryview)):
            return content
        return content.encode(self.charset)  # type: ignore

    def init_headers(self, headers: typing.Mapping[str, str] | None = None) -> None:
        if headers is None:
            raw_headers: dict = {}
            populate_content_length = True
            populate_content_type = True
        else:
            raw_headers = {k.lower(): v for k, v in headers.items()}
            keys = raw_headers.keys()
            populate_content_length = "content-length" not in keys
            populate_content_type = "content-type" not in keys

        body = getattr(self, "body", None)
        if body is not None and populate_content_length and not (self.status_code < 200 or self.status_code in (204, 304)):
            content_length = str(len(body))
            raw_headers.setdefault("content-length", content_length)

        content_type = self.media_type
        if content_type is not None and populate_content_type:
            if content_type.startswith("text/") and "charset=" not in content_type.lower():
                content_type += "; charset=" + self.charset
            raw_headers.setdefault("content-type", content_type)

        self.raw_headers = raw_headers


def to_response(cls):
    class ResponseWrapper(cls):
        def __new__(cls, *args, **kwargs):
            instance = super().__new__(cls)
            instance.__init__(*args, **kwargs)
            headers = Headers(instance.raw_headers)
            return RobynResponse(
                status_code=instance.status_code,
                headers=headers,
                description=instance.body,
            )

    return ResponseWrapper


@to_response
class JSONResponse(Response):
    media_type = "application/json"


@to_response
class HTMLResponse(Response):
    media_type = "text/html"


@to_response
class PlainTextResponse(Response):
    media_type = "text/plain"


@to_response
class RedirectResponse(Response):
    def __init__(
        self,
        url: str,
        status_code: int = 307,
        headers: typing.Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(content=b"", status_code=status_code, headers=headers)
        self.raw_headers["location"] = quote(str(url), safe=":/%#?=@[]!$&'()*+,;")
