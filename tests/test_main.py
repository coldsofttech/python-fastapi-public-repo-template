import pytest
import uvicorn
from fastapi.testclient import TestClient

from example_api import __main__ as entrypoint
from example_api.config import Settings
from example_api.main import create_app


def test_cors_origins_enable_cors_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "example_api.main.get_settings",
        lambda: Settings(_env_file=None, cors_origins=["https://a.example"]),
    )

    response = TestClient(create_app()).get("/health", headers={"Origin": "https://a.example"})

    assert response.headers["access-control-allow-origin"] == "https://a.example"


def test_main_runs_uvicorn_with_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(entrypoint, "get_settings", lambda: Settings(_env_file=None, port=9001))
    monkeypatch.setattr(uvicorn, "run", lambda app, **kwargs: calls.append((app, kwargs)))

    entrypoint.main()

    assert calls == [
        (
            "example_api.main:app",
            {
                "host": "127.0.0.1",
                "port": 9001,
                "workers": 1,
                "timeout_graceful_shutdown": 10,
                "log_config": None,
                "proxy_headers": True,
                "forwarded_allow_ips": "127.0.0.1",
            },
        )
    ]
