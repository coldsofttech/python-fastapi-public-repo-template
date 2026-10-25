"""Version 1 of the API, served under ``/api/v1``."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from example_api.auth import Principal, authenticate
from example_api.schemas import HelloResponse, WhoAmIResponse
from example_package import greet

router = APIRouter(tags=["v1"])


# A plain ``def`` handler runs in a worker thread, so blocking library calls are safe.
# Use ``async def`` only when everything inside is awaited.
@router.get(
    "/hello/{name}",
    summary="Greet someone",
    responses={422: {"description": "Invalid name."}},
)
def hello(name: Annotated[str, Path(description="Who to greet.")]) -> HelloResponse:
    """Return a greeting. Public: no authentication required."""
    try:
        return HelloResponse(message=greet(name))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get(
    "/whoami",
    summary="Show the caller",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Authentication failed."}},
)
def whoami(principal: Annotated[Principal, Depends(authenticate)]) -> WhoAmIResponse:
    """Return the authenticated caller. Protected according to ``EXAMPLE_API_AUTH_MODE``."""
    return WhoAmIResponse(subject=principal.subject, method=principal.method)
