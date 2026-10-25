import pytest
import uvicorn
from fastapi.testclient import TestClient

from example_api import __main__ as entrypoint
from example_api.config import Settings
from example_api.main import create_app


def _client(monkeypatch: pytest.MonkeyPatch, **settings: object) -> TestClient:
    monkeypatch.setattr(
        "example_api.main.get_settings",
        lambda: Settings(_env_file=None, **settings),  # type: ignore[arg-type]
    )
    return TestClient(create_app(), base_url="http://api.example.com")


def test_any_host_is_accepted_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _client(monkeypatch).get("/health").status_code == 200


def test_allowed_hosts_accepts_listed_host(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch, allowed_hosts=["api.example.com"])

    assert client.get("/health").status_code == 200


def test_allowed_hosts_rejects_other_hosts(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch, allowed_hosts=["other.example.com"])

    assert client.get("/health").status_code == 400


def test_root_path_is_reflected_in_openapi(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch, root_path="/myapi")

    assert client.get("/openapi.json").json()["servers"] == [{"url": "/myapi"}]


def test_main_passes_proxy_settings_to_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        entrypoint,
        "get_settings",
        lambda: Settings(_env_file=None, forwarded_allow_ips="10.0.0.0/8"),
    )
    monkeypatch.setattr(uvicorn, "run", lambda app, **kwargs: calls.append(kwargs))

    entrypoint.main()

    assert calls[0]["proxy_headers"] is True
    assert calls[0]["forwarded_allow_ips"] == "10.0.0.0/8"
