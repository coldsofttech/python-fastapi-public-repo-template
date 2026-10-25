import httpx

import example_package


def test_health(base_url: str) -> None:
    assert httpx.get(f"{base_url}/health").json() == {"status": "ok"}


def test_ready_reports_version(base_url: str) -> None:
    assert httpx.get(f"{base_url}/ready").json()["version"] == example_package.__version__


def test_hello(base_url: str) -> None:
    assert httpx.get(f"{base_url}/api/v1/hello/Ada").json() == {"message": "Hello, Ada!"}


def test_request_id_header(base_url: str) -> None:
    assert "x-request-id" in httpx.get(f"{base_url}/health").headers


def test_security_headers(base_url: str) -> None:
    assert httpx.get(f"{base_url}/health").headers["x-content-type-options"] == "nosniff"


def test_docs_are_served(base_url: str) -> None:
    assert httpx.get(f"{base_url}/docs").status_code == 200
