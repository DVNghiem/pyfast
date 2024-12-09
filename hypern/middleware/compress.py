import gzip
import zlib
from typing import List, Optional

from hypern.hypern import Request, Response

from .base import Middleware, MiddlewareConfig


class CompressionMiddleware(Middleware):
    """
    Middleware for compressing response content using gzip or deflate encoding.
    """

    def __init__(
        self, config: Optional[MiddlewareConfig] = None, min_size: int = 500, compression_level: int = 6, include_types: Optional[List[str]] = None
    ) -> None:
        """
        Initialize compression middleware.

        Args:
            min_size: Minimum response size in bytes to trigger compression
            compression_level: Compression level (1-9, higher = better compression but slower)
            include_types: List of content types to compress (defaults to common text types)
        """
        super().__init__(config)
        self.min_size = min_size
        self.compression_level = compression_level
        self.include_types = include_types or [
            "text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
            "application/json",
            "application/xml",
            "application/x-yaml",
        ]

    def before_request(self, request: Request) -> Request:
        return request

    def after_request(self, response: Response) -> Response:
        # Check if response should be compressed
        content_type = (response.headers.get("content-type") or "").split(";")[0].lower()
        content_encoding = (response.headers.get("content-encoding") or "").lower()

        # Skip if:
        # - Content is already encoded
        # - Content type is not in include list
        # - Content length is below minimum size
        if content_encoding or content_type not in self.include_types or len(response.description.encode()) < self.min_size:
            return response

        # Get accepted encodings from request
        accept_encoding = (response.headers.get("accept-encoding") or "").lower()

        if "gzip" in accept_encoding:
            # Use gzip compression
            response.description = gzip.compress(
                response.description if isinstance(response.description, bytes) else str(response.description).encode(), compresslevel=self.compression_level
            )
            response.headers.set("content-encoding", "gzip")

        elif "deflate" in accept_encoding:
            # Use deflate compression
            response.description = zlib.compress(
                response.description if isinstance(response.description, bytes) else str(response.description).encode(), level=self.compression_level
            )
            response.headers.set("content-encoding", "deflate")

        # Update content length after compression
        response.headers.set("content-length", str(len(response.description)))

        # Add Vary header to indicate content varies by Accept-Encoding
        response.headers.set("vary", "Accept-Encoding")

        return response
