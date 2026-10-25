"""Per-client rate limiting, kept in memory.

Requests are counted per client address in fixed windows. The counters live in one process, so with
several instances each one enforces its own limit. When you need an exact global limit, enforce it
at the proxy or API gateway, or back the limiter with a shared store such as Redis.

Behind a reverse proxy the client address comes from ``X-Forwarded-For``, but only when the proxy is
listed in ``EXAMPLE_API_FORWARDED_ALLOW_IPS``. Otherwise every request would look like the proxy.
"""

import math
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from example_api.errors import problem

EXEMPT_PATHS = frozenset({"/health", "/ready"})
WINDOW_SECONDS = 60.0
MAX_TRACKED_CLIENTS = 10_000


@dataclass(frozen=True)
class Decision:
    """The outcome of counting one request."""

    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int


class RateLimiter:
    """Fixed-window counter per key."""

    def __init__(
        self,
        limit: int,
        window: float = WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._limit = limit
        self._window = window
        self._clock = clock
        self._windows: dict[str, tuple[float, int]] = {}

    def hit(self, key: str) -> Decision:
        """Count a request for ``key`` and say whether it is within the limit."""
        now = self._clock()
        start, count = self._windows.get(key, (now, 0))
        if now - start >= self._window:
            start, count = now, 0
        count += 1
        self._windows[key] = (start, count)
        if len(self._windows) > MAX_TRACKED_CLIENTS:
            self._prune(now)
        return Decision(
            allowed=count <= self._limit,
            limit=self._limit,
            remaining=max(0, self._limit - count),
            reset_seconds=max(1, math.ceil(start + self._window - now)),
        )

    def _prune(self, now: float) -> None:
        """Drop expired windows. If a flood of new addresses fills memory, start over."""
        self._windows = {k: v for k, v in self._windows.items() if now - v[0] < self._window}
        if len(self._windows) > MAX_TRACKED_CLIENTS:
            self._windows.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Reject clients that exceed the limit with ``429`` and ``Retry-After``."""

    def __init__(self, app: ASGIApp, limiter: RateLimiter) -> None:
        super().__init__(app)
        self._limiter = limiter

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        key = request.client.host if request.client else "unknown"
        decision = self._limiter.hit(key)
        headers = {
            "X-RateLimit-Limit": str(decision.limit),
            "X-RateLimit-Remaining": str(decision.remaining),
            "X-RateLimit-Reset": str(decision.reset_seconds),
        }
        if not decision.allowed:
            headers["Retry-After"] = str(decision.reset_seconds)
            return problem(429, "Too many requests. Try again later.", headers=headers)
        response = await call_next(request)
        response.headers.update(headers)
        return response
