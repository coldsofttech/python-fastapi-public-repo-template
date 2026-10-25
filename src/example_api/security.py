"""Baseline protections: response headers and a request size limit.

HTTPS itself, request timeouts and connection limits belong to the reverse proxy or load balancer.
"""

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from example_api.errors import problem

# The interactive docs load scripts and styles, so a strict policy would break them.
DOCS_PREFIXES = ("/docs", "/redoc")
API_CSP = "default-src 'none'; frame-ancestors 'none'"
HSTS = "max-age=31536000; includeSubDomains"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add headers that stop browsers from guessing types, framing or caching API responses."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "no-referrer")
        path = request.url.path
        if not path.startswith(DOCS_PREFIXES):
            headers.setdefault("Content-Security-Policy", API_CSP)
        if path.startswith("/api/"):
            headers.setdefault("Cache-Control", "no-store")
        # Only meaningful over HTTPS. The scheme is correct behind a proxy that is trusted.
        if request.url.scheme == "https":
            headers.setdefault("Strict-Transport-Security", HSTS)
        return response


class BodyLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose declared ``Content-Length`` is above the limit with ``413``.

    Chunked uploads have no declared length, so also set a body size limit at the proxy.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        super().__init__(app)
        self._max_bytes = max_bytes

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        declared = request.headers.get("content-length", "")
        if declared.isdigit() and int(declared) > self._max_bytes:
            return problem(413, f"Request body is larger than {self._max_bytes} bytes.")
        return await call_next(request)
