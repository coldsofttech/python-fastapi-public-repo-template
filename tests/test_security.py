import pytest
from fastapi.testclient import TestClient

from example_api.config import Settings
from example_api.main import create_app
from example_api.ratelimit import RateLimiter


def _client(
    monkeypatch: pytest.MonkeyPatch, base_url: str = "http://testserver", **s: object
) -> TestClient:
    monkeypatch.setattr(
        "example_api.main.get_settings",
        lambda: Settings(_env_file=None, **s),  # type: ignore[arg-type]
    )
    return TestClient(create_app(), base_url=base_url)


def test_security_headers_on_api_responses(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _client(monkeypatch).get("/api/v1/hello/Ada")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"


def test_hsts_only_over_https(monkeypatch: pytest.MonkeyPatch) -> None:
    http = _client(monkeypatch).get("/health")
    https = _client(monkeypatch, base_url="https://api.example.com").get("/health")

    assert "strict-transport-security" not in http.headers
    assert "includeSubDomains" in https.headers["strict-transport-security"]


def test_docs_page_is_not_given_a_strict_csp(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _client(monkeypatch).get("/docs")

    assert response.status_code == 200
    assert "content-security-policy" not in response.headers


def test_oversized_body_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch, max_body_bytes=100)

    response = client.request("GET", "/api/v1/hello/Ada", content=b"x" * 101)

    assert response.status_code == 413
    assert response.headers["content-type"] == "application/problem+json"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_rate_limit_returns_429_with_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch, rate_limit_per_minute=2)

    first = client.get("/api/v1/hello/Ada")
    client.get("/api/v1/hello/Ada")
    third = client.get("/api/v1/hello/Ada")

    assert first.headers["x-ratelimit-limit"] == "2"
    assert first.headers["x-ratelimit-remaining"] == "1"
    assert third.status_code == 429
    assert third.headers["content-type"] == "application/problem+json"
    assert int(third.headers["retry-after"]) >= 1
    assert third.headers["x-request-id"]


def test_health_probes_are_never_rate_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch, rate_limit_per_minute=1)

    assert all(client.get(path).status_code == 200 for path in ["/health", "/ready"] * 5)


def test_rate_limit_can_be_turned_off(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch, rate_limit_per_minute=0)

    assert all(client.get("/api/v1/hello/Ada").status_code == 200 for _ in range(10))
    assert "x-ratelimit-limit" not in client.get("/api/v1/hello/Ada").headers


def test_docs_can_be_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch, docs_enabled=False)

    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404
    assert client.get("/health").status_code == 200


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_limiter_counts_per_client_and_resets_after_the_window() -> None:
    clock = _Clock()
    limiter = RateLimiter(limit=2, window=60, clock=clock)

    assert limiter.hit("a").allowed
    assert limiter.hit("a").allowed
    blocked = limiter.hit("a")
    assert not blocked.allowed
    assert blocked.reset_seconds == 60
    assert limiter.hit("b").allowed

    clock.now += 61
    assert limiter.hit("a").allowed


def test_limiter_does_not_grow_without_bound(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("example_api.ratelimit.MAX_TRACKED_CLIENTS", 5)
    clock = _Clock()
    limiter = RateLimiter(limit=1, window=60, clock=clock)

    for i in range(20):
        limiter.hit(f"client-{i}")

    assert len(limiter._windows) <= 5
