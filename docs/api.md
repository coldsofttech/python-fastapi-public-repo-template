# API reference

`example-api` is an HTTP API built with [FastAPI](https://fastapi.tiangolo.com/). Rename it and replace the example routes with your own.

The machine-readable contract is [openapi.json](openapi.json). While the server runs, interactive docs are at `/docs` (Swagger UI) and `/redoc`, and the live contract is at `/openapi.json`.

## Running

```bash
uv run example-api                   # starts uvicorn using the settings below
uv run uvicorn example_api.main:app --reload   # auto-reload for development
docker compose up --build            # in a container
```

## Endpoints

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/health` | none | Liveness probe. Returns 200 while the process runs. |
| `GET` | `/ready` | none | Readiness probe. Returns 200 and the version when the service can take traffic. |
| `GET` | `/api/v1/hello/{name}` | none | Greeting. Returns 422 for a blank name. |
| `GET` | `/api/v1/whoami` | per `AUTH_MODE` | Shows who the caller is. Returns 401 if authentication fails. |

Versioned routes live under `/api/v1`. Add `/api/v2` as a new router when you need a breaking change, and keep `v1` running until callers have moved.

## Configuration

Settings come from environment variables prefixed `EXAMPLE_API_`, or from a `.env` file (see `.env.example`). List values are JSON.

| Variable | Default | Description |
| --- | --- | --- |
| `EXAMPLE_API_HOST` | `127.0.0.1` | Interface to listen on. The Docker image sets `0.0.0.0`. |
| `EXAMPLE_API_PORT` | `8000` | Port to listen on. |
| `EXAMPLE_API_LOG_LEVEL` | `info` | Log level. |
| `EXAMPLE_API_WORKERS` | `1` | Server processes. Prefer more containers; see [deployment](deployment.md). |
| `EXAMPLE_API_SHUTDOWN_TIMEOUT` | `10` | Seconds to let in-flight requests finish when the server stops. |
| `EXAMPLE_API_DOCS_ENABLED` | `true` | Serve `/docs`, `/redoc` and `/openapi.json`. The Docker image sets `false`. |
| `EXAMPLE_API_RATE_LIMIT_PER_MINUTE` | `120` | Requests per client address per minute. `0` turns the limit off. |
| `EXAMPLE_API_MAX_BODY_BYTES` | `1048576` | Largest accepted request body. |
| `EXAMPLE_API_CORS_ORIGINS` | `[]` | Allowed browser origins. CORS is off when empty. |
| `EXAMPLE_API_ALLOWED_HOSTS` | `[]` | Accepted `Host` header values (your domains). Any host is accepted when empty. |
| `EXAMPLE_API_ROOT_PATH` | empty | Path prefix when a proxy serves the API under a sub-path, such as `/myapi`. |
| `EXAMPLE_API_FORWARDED_ALLOW_IPS` | `127.0.0.1` | Proxy addresses whose `X-Forwarded-*` headers are trusted. Use `*` only if the API is unreachable except through the proxy. |
| `EXAMPLE_API_AUTH_MODE` | `none` | `none`, `api_key` or `jwt`. See below. |
| `EXAMPLE_API_API_KEYS` | `[]` | Accepted keys when the mode is `api_key`. |
| `EXAMPLE_API_JWT_KEY` | | Key used to verify tokens when the mode is `jwt`. |
| `EXAMPLE_API_JWT_ALGORITHM` | `HS256` | Token signing algorithm. |
| `EXAMPLE_API_JWT_AUDIENCE` | | Required `aud` claim, if set. |
| `EXAMPLE_API_JWT_ISSUER` | | Required `iss` claim, if set. |

The domain name, DNS and HTTPS are not configured in the app. See [deployment](deployment.md).

Misconfigured authentication, such as `api_key` mode with no keys, stops the server at startup instead of failing on the first request.

## Authentication

Protected routes depend on `authenticate` in `example_api/auth.py`. Choose a mode with `EXAMPLE_API_AUTH_MODE`.

| Mode | Caller sends | Use it for |
| --- | --- | --- |
| `none` | nothing | Local development. Every caller is anonymous. |
| `api_key` | `X-API-Key: <key>` | Service-to-service calls and simple integrations. Keys are compared in constant time. |
| `jwt` | `Authorization: Bearer <token>` | Tokens issued by an identity provider. Tokens must carry `exp` and `sub`. |

Notes:

- Rotate API keys by listing the old and new key together, then removing the old one.
- For JWT in production, use an asymmetric algorithm such as `RS256` and set `EXAMPLE_API_JWT_KEY` to the provider's public key, so the API can verify tokens but never sign them.
- Always serve the API over HTTPS, for example behind a reverse proxy or load balancer.
- To protect a whole router, add `dependencies=[Depends(authenticate)]` to it.

## Errors

Every error uses the [problem details](https://www.rfc-editor.org/rfc/rfc9457) format with the content type `application/problem+json`:

```json
{"type": "about:blank", "title": "Unprocessable Content", "status": 422, "detail": "name must not be empty"}
```

Validation errors add an `errors` list. Rate-limited requests get `429` with a `Retry-After` header, and oversized bodies get `413`. Protections are described in [security](security.md). Unexpected errors return a bare `500` with no details, and the full error is written to the log with the request ID.

## Logging and request IDs

Logs are JSON, one object per line, on stdout. Every response carries an `X-Request-ID` header. A caller can send its own ID, and it appears in every log line for that request.

## Adding an endpoint

1. Add the logic to `example_package` as a plain function. It must not know about HTTP.
2. Add a response model to `schemas.py` and a route to a router in `routers/` that calls the function. Use `def` for blocking work and `async def` only when everything inside is awaited.
3. Add tests with `TestClient` in `tests/`, and an HTTP test in `tests/integration/` if it needs the real server.
4. Regenerate the contract and commit it: `uv run python scripts/export_openapi.py`. CI fails if `openapi.json` is out of date.
