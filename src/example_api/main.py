"""Application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from example_api.config import get_settings
from example_api.errors import register_error_handlers
from example_api.logs import RequestIdMiddleware, configure_logging
from example_api.ratelimit import RateLimiter, RateLimitMiddleware
from example_api.routers import health, v1
from example_api.security import BodyLimitMiddleware, SecurityHeadersMiddleware
from example_package import __version__


def create_app() -> FastAPI:
    """Build the application. Tests call this to get a fresh app."""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="example-api",
        version=__version__,
        root_path=settings.root_path,
        description="Example HTTP API built on **example_package**.",
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )

    # Middleware added last runs first, so the order below reads from innermost to outermost:
    # rate limit, body limit, security headers, request ID, CORS, allowed hosts.
    if settings.rate_limit_per_minute > 0:
        limiter = RateLimiter(settings.rate_limit_per_minute)
        app.add_middleware(RateLimitMiddleware, limiter=limiter)
    app.add_middleware(BodyLimitMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET"],
            allow_headers=["Authorization", "Content-Type", "X-API-Key"],
        )
    if settings.allowed_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(v1.router, prefix="/api/v1")
    return app


app = create_app()
