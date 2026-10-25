import pytest
from fastapi.testclient import TestClient

import example_package


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_version(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "version": example_package.__version__}


def test_hello(client: TestClient) -> None:
    response = client.get("/api/v1/hello/Ada")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello, Ada!"}


def test_hello_blank_name_is_a_problem(client: TestClient) -> None:
    response = client.get("/api/v1/hello/%20")

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["detail"] == "name must not be empty"


def test_unknown_route_is_a_problem(client: TestClient) -> None:
    response = client.get("/nope")

    assert response.status_code == 404
    assert response.json()["title"] == "Not Found"


def test_request_id_is_generated(client: TestClient) -> None:
    response = client.get("/health")

    assert len(response.headers["x-request-id"]) == 32


def test_request_id_is_reused(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "abc-123"})

    assert response.headers["x-request-id"] == "abc-123"


def test_openapi_describes_the_api(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()

    assert spec["info"]["version"] == example_package.__version__
    assert "/api/v1/hello/{name}" in spec["paths"]


def test_unexpected_error_hides_details(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(name: str) -> str:
        raise RuntimeError("secret detail")

    monkeypatch.setattr("example_api.routers.v1.greet", boom)

    response = client.get("/api/v1/hello/Ada")

    assert response.status_code == 500
    assert response.json() == {
        "type": "about:blank",
        "title": "Internal Server Error",
        "status": 500,
    }
    assert "secret detail" not in response.text


def test_cors_is_off_by_default(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "https://a.example"})

    assert "access-control-allow-origin" not in response.headers
