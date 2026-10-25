import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator

import httpx
import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark every test in this directory as an integration test."""
    for item in items:
        if "integration" in item.path.parts:
            item.add_marker(pytest.mark.integration)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    """Run the real server in a subprocess, the way users start it."""
    port = _free_port()
    env = {
        **os.environ,
        "EXAMPLE_API_PORT": str(port),
        "EXAMPLE_API_HOST": "127.0.0.1",
        # Fuzzing sends many requests from one address.
        "EXAMPLE_API_RATE_LIMIT_PER_MINUTE": "0",
    }
    process = subprocess.Popen([sys.executable, "-m", "example_api"], env=env)
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail("server exited during startup")
            try:
                if httpx.get(f"{url}/health", timeout=1).status_code == 200:
                    break
            except httpx.TransportError:
                time.sleep(0.2)
        else:
            pytest.fail("server did not become ready")
        yield url
    finally:
        process.terminate()
        process.wait(timeout=10)
