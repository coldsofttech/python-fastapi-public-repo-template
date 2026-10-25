from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from example_api.config import AuthMode, Settings, get_settings
from example_api.main import create_app

ClientFactory = Callable[..., TestClient]


@pytest.fixture
def make_client() -> ClientFactory:
    """Build a client for an app with the given settings, ignoring the environment."""

    def factory(**settings: object) -> TestClient:
        app = create_app()
        app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, **settings)  # type: ignore[arg-type]
        return TestClient(app, raise_server_exceptions=False)

    return factory


@pytest.fixture
def client(make_client: ClientFactory) -> TestClient:
    return make_client(auth_mode=AuthMode.NONE)
