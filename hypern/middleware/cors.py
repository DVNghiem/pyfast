from typing import List, Optional
from .base import Middleware
from hypern.hypern import MiddlewareConfig


class CORSMiddleware(Middleware):
    """
    The `CORSMiddleware` class is used to add CORS headers to the response based on specified origins,
    methods, and headers.
    """

    def __init__(
        self, config: Optional[MiddlewareConfig] = None, allow_origins: List[str] = None, allow_methods: List[str] = None, allow_headers: List[str] = None
    ) -> None:
        super().__init__(config)
        self.allow_origins = allow_origins or []
        self.allow_methods = allow_methods or []
        self.allow_headers = allow_headers or []

    def before_request(self, request):
        return request

    def after_request(self, response):
        """
        The `after_request` function adds Access-Control headers to the response based on specified origins,
        methods, and headers.

        :param response: The `after_request` method is used to add CORS (Cross-Origin Resource Sharing)
        headers to the response object before sending it back to the client. The parameters used in this
        method are:
        :return: The `response` object is being returned from the `after_request` method.
        """
        for origin in self.allow_origins:
            self.app.add_response_header("Access-Control-Allow-Origin", origin)
            self.app.add_response_header(
                "Access-Control-Allow-Methods",
                ", ".join([method.upper() for method in self.allow_methods]),
            )
            self.app.add_response_header("Access-Control-Allow-Headers", ", ".join(self.allow_headers))
            self.app.add_response_header("Access-Control-Allow-Credentials", "true")
        return response
