"""Liveness and readiness probes, used by load balancers and container platforms."""

from fastapi import APIRouter

from example_api.schemas import HealthResponse, ReadyResponse
from example_package import __version__

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> HealthResponse:
    """Return 200 while the process is running."""
    return HealthResponse()


@router.get("/ready", summary="Readiness probe")
async def ready() -> ReadyResponse:
    """Return 200 when the service can take traffic. Add checks for your dependencies here."""
    return ReadyResponse(version=__version__)
