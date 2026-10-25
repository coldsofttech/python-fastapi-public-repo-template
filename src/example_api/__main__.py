"""Start the server with ``example-api`` or ``python -m example_api``."""

import uvicorn

from example_api.config import get_settings


def main() -> None:
    """Run uvicorn with the host, port, worker and proxy settings."""
    settings = get_settings()
    # log_config=None keeps uvicorn's logs on our JSON handler. Forwarded headers are only
    # trusted from forwarded_allow_ips, so a client cannot spoof its address.
    uvicorn.run(
        "example_api.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        timeout_graceful_shutdown=settings.shutdown_timeout,
        log_config=None,
        proxy_headers=True,
        forwarded_allow_ips=settings.forwarded_allow_ips,
    )


if __name__ == "__main__":
    main()
