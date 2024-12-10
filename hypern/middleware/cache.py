import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional

from hypern.hypern import Header, MiddlewareConfig, Request, Response

from .base import Middleware


class CacheConfig:
    """
    Configuration class for caching middleware.

    Attributes:
        max_age (int): The maximum age (in seconds) for the cache. Default is 3600 seconds (1 hour).
        s_maxage (Optional[int]): The shared maximum age (in seconds) for the cache. Default is None.
        stale_while_revalidate (Optional[int]): The time (in seconds) the cache can be used while revalidation is performed. Default is None.
        stale_if_error (Optional[int]): The time (in seconds) the cache can be used if an error occurs during revalidation. Default is None.
        vary_by (List[str]): List of headers to vary the cache by. Default is ['Accept', 'Accept-Encoding'].
        cache_control (List[str]): List of cache control directives. Default is an empty list.
        include_query_string (bool): Whether to include the query string in the cache key. Default is True.
        exclude_paths (List[str]): List of paths to exclude from caching. Default is ['/admin', '/api/private'].
        exclude_methods (List[str]): List of HTTP methods to exclude from caching. Default is ['POST', 'PUT', 'DELETE', 'PATCH'].
        private_paths (List[str]): List of paths to be marked as private. Default is an empty list.
        cache_by_headers (List[str]): List of headers to include in the cache key. Default is an empty list.
    """

    def __init__(
        self,
        max_age: int = 3600,  # 1 hour default
        s_maxage: Optional[int] = None,
        stale_while_revalidate: Optional[int] = None,
        stale_if_error: Optional[int] = None,
        vary_by: List[str] = None,
        cache_control: List[str] = None,
        include_query_string: bool = True,
        exclude_paths: List[str] = None,
        exclude_methods: List[str] = None,
        private_paths: List[str] = None,
        cache_by_headers: List[str] = None,
    ):
        self.max_age = max_age
        self.s_maxage = s_maxage
        self.stale_while_revalidate = stale_while_revalidate
        self.stale_if_error = stale_if_error
        self.vary_by = vary_by or ["accept", "accept-encoding"]
        self.cache_control = cache_control or []
        self.include_query_string = include_query_string
        self.exclude_paths = exclude_paths or ["/admin", "/api/private"]
        self.exclude_methods = exclude_methods or ["POST", "PUT", "DELETE", "PATCH"]
        self.private_paths = private_paths or []
        self.cache_by_headers = cache_by_headers or []


class EdgeCacheMiddleware(Middleware):
    """
    Middleware implementing edge caching strategies with support for:
    - Cache-Control directives
    - ETag generation
    - Conditional requests (If-None-Match, If-Modified-Since)
    - Vary header management
    - CDN-specific headers
    """

    def __init__(self, cache_config: CacheConfig | None = None, config: Optional[MiddlewareConfig] = None):
        super().__init__(config)
        self.cache_config = cache_config or CacheConfig()
        self._etag_cache: Dict[str, str] = {}
        self.request_context = {}

    def _should_cache(self, request: Request, path: str) -> bool:
        """Determine if the request should be cached"""
        if request.method in self.cache_config.exclude_methods:
            return False

        if any(excluded in path for excluded in self.cache_config.exclude_paths):
            return False

        return True

    def _generate_cache_key(self, request: Request) -> str:
        """Generate a unique cache key based on request attributes"""
        components = [request.method, request.path]

        if self.cache_config.include_query_string:
            components.append(str(request.query_params))

        for header in self.cache_config.cache_by_headers:
            value = request.headers.get(str(header).lower())
            if value:
                components.append(f"{header}:{value}")

        return hashlib.sha256(":".join(components).encode()).hexdigest()

    def _generate_etag(self, response: Response) -> str:
        """Generate ETag for response content"""
        content = response.description
        if not isinstance(content, bytes):
            content = str(content).encode()
        return hashlib.sha256(content).hexdigest()

    def _build_cache_control(self, path: str) -> str:
        """Build Cache-Control header value"""
        directives = []

        # Determine public/private caching
        if any(private in path for private in self.cache_config.private_paths):
            directives.append("private")
        else:
            directives.append("public")

        # Add max-age directives
        directives.append(f"max-age={self.cache_config.max_age}")

        if self.cache_config.s_maxage is not None:
            directives.append(f"s-maxage={self.cache_config.s_maxage}")

        if self.cache_config.stale_while_revalidate is not None:
            directives.append(f"stale-while-revalidate={self.cache_config.stale_while_revalidate}")

        if self.cache_config.stale_if_error is not None:
            directives.append(f"stale-if-error={self.cache_config.stale_if_error}")

        # Add custom cache control directives
        directives.extend(self.cache_config.cache_control)

        return ", ".join(directives)

    def cleanup_context(self, context_id: str):
        try:
            del self.request_context[context_id]
        except Exception:
            pass

    def before_request(self, request: Request) -> Request | Response:
        """Handle conditional requests"""
        if not self._should_cache(request, request.path):
            return request

        cache_key = self._generate_cache_key(request)
        etag = self._etag_cache.get(cache_key)

        if etag:
            if_none_match = request.headers.get("if-none-match")
            if if_none_match and if_none_match == etag:
                return Response(status_code=304, description=b"", headers=Header({"ETag": etag}))
        self.request_context[request.context_id] = request
        return request

    def after_request(self, response: Response) -> Response:
        """Add caching headers to response"""
        request = self.request_context.get(response.context_id)
        self.cleanup_context(response.context_id)
        if not self._should_cache(request, request.path):
            response.headers.set("Cache-Control", "no-store")
            return response

        # Generate and store ETag
        cache_key = self._generate_cache_key(request)
        etag = self._generate_etag(response)
        self._etag_cache[cache_key] = etag

        # Set cache headers
        response.headers.update(
            {
                "Cache-Control": self._build_cache_control(request.path),
                "ETag": etag,
                "Vary": ", ".join(self.cache_config.vary_by),
                "Last-Modified": datetime.now(tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
            }
        )

        # Add CDN-specific headers
        response.headers.set("CDN-Cache-Control", response.headers["Cache-Control"])
        response.headers.set("Surrogate-Control", f"max-age={self.cache_config.s_maxage or self.cache_config.max_age}")

        return response
