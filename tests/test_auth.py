import time
from collections.abc import Callable

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from example_api.config import AuthMode, Settings

ClientFactory = Callable[..., TestClient]
JWT_KEY = "test-signing-key-with-at-least-32-bytes"


def _token(**claims: object) -> str:
    payload = {"sub": "ada", "exp": int(time.time()) + 60, **claims}
    return jwt.encode(payload, JWT_KEY, algorithm="HS256")


def test_none_mode_is_anonymous(make_client: ClientFactory) -> None:
    response = make_client(auth_mode=AuthMode.NONE).get("/api/v1/whoami")

    assert response.json() == {"subject": "anonymous", "method": "none"}


def test_api_key_accepts_valid_key(make_client: ClientFactory) -> None:
    client = make_client(auth_mode=AuthMode.API_KEY, api_keys=[SecretStr("k1"), SecretStr("k2")])

    response = client.get("/api/v1/whoami", headers={"X-API-Key": "k2"})

    assert response.status_code == 200
    assert response.json() == {"subject": "api-key", "method": "api_key"}


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong"}])
def test_api_key_rejects_missing_or_wrong_key(
    make_client: ClientFactory, headers: dict[str, str]
) -> None:
    client = make_client(auth_mode=AuthMode.API_KEY, api_keys=[SecretStr("k1")])

    response = client.get("/api/v1/whoami", headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "ApiKey"
    assert response.headers["content-type"] == "application/problem+json"


def test_public_route_needs_no_credentials(make_client: ClientFactory) -> None:
    client = make_client(auth_mode=AuthMode.API_KEY, api_keys=[SecretStr("k1")])

    assert client.get("/api/v1/hello/Ada").status_code == 200


def test_jwt_accepts_valid_token(make_client: ClientFactory) -> None:
    client = make_client(auth_mode=AuthMode.JWT, jwt_key=SecretStr(JWT_KEY))

    response = client.get("/api/v1/whoami", headers={"Authorization": f"Bearer {_token()}"})

    assert response.status_code == 200
    assert response.json() == {"subject": "ada", "method": "jwt"}


def _foreign_token() -> str:
    """A well-formed token signed with a key the server does not know."""
    claims = {"sub": "x", "exp": int(time.time()) + 60}
    return jwt.encode(claims, "a-different-key-with-32-bytes-or-more!", algorithm="HS256")


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer not-a-token"},
        {"Authorization": f"Bearer {_token(exp=int(time.time()) - 60)}"},
        {"Authorization": f"Bearer {_foreign_token()}"},
    ],
)
def test_jwt_rejects_bad_tokens(make_client: ClientFactory, headers: dict[str, str]) -> None:
    client = make_client(auth_mode=AuthMode.JWT, jwt_key=SecretStr(JWT_KEY))

    response = client.get("/api/v1/whoami", headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_jwt_checks_audience_and_issuer(make_client: ClientFactory) -> None:
    client = make_client(
        auth_mode=AuthMode.JWT,
        jwt_key=SecretStr(JWT_KEY),
        jwt_audience="my-api",
        jwt_issuer="https://issuer.example",
    )
    good = _token(aud="my-api", iss="https://issuer.example")
    wrong_audience = _token(aud="other", iss="https://issuer.example")

    assert (
        client.get("/api/v1/whoami", headers={"Authorization": f"Bearer {good}"}).status_code == 200
    )
    assert (
        client.get(
            "/api/v1/whoami", headers={"Authorization": f"Bearer {wrong_audience}"}
        ).status_code
        == 401
    )


@pytest.mark.parametrize("mode", [AuthMode.API_KEY, AuthMode.JWT])
def test_misconfigured_auth_fails_at_startup(mode: AuthMode) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, auth_mode=mode)
