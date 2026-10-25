"""Authentication for protected routes.

The mode is chosen with ``EXAMPLE_API_AUTH_MODE``:

- ``none``: every request is anonymous (default, for local development).
- ``api_key``: callers send a shared secret in the ``X-API-Key`` header. Suited to
  service-to-service calls.
- ``jwt``: callers send ``Authorization: Bearer <token>``. Suited to user tokens issued by an
  identity provider. Use an asymmetric algorithm (for example ``RS256``) and the provider's public
  key in production.
"""

import secrets
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from example_api.config import AuthMode, Settings, get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    """Who made the request."""

    subject: str
    method: str


def _unauthorized(detail: str, scheme: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": scheme},
    )


def _check_api_key(settings: Settings, api_key: str | None) -> Principal:
    if api_key is not None and any(
        secrets.compare_digest(api_key.encode(), key.get_secret_value().encode())
        for key in settings.api_keys
    ):
        return Principal(subject="api-key", method=AuthMode.API_KEY)
    raise _unauthorized("Invalid or missing API key.", "ApiKey")


def _check_jwt(settings: Settings, credentials: HTTPAuthorizationCredentials | None) -> Principal:
    if credentials is None:
        raise _unauthorized("Missing bearer token.", "Bearer")
    if settings.jwt_key is None:  # Prevented by the settings validator.
        raise RuntimeError("jwt_key is not configured")
    try:
        claims = jwt.decode(
            credentials.credentials,
            key=settings.jwt_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError as exc:
        raise _unauthorized("Invalid token.", "Bearer") from exc
    return Principal(subject=str(claims["sub"]), method=AuthMode.JWT)


def authenticate(
    settings: Annotated[Settings, Depends(get_settings)],
    api_key: Annotated[str | None, Security(_api_key_header)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer)],
) -> Principal:
    """Dependency that returns the caller, or raises 401."""
    if settings.auth_mode is AuthMode.API_KEY:
        return _check_api_key(settings, api_key)
    if settings.auth_mode is AuthMode.JWT:
        return _check_jwt(settings, credentials)
    return Principal(subject="anonymous", method=AuthMode.NONE)
