# python-fastapi-public-repo-template

[![CI](https://github.com/coldsofttech/python-fastapi-public-repo-template/actions/workflows/ci.yml/badge.svg)](https://github.com/coldsofttech/python-fastapi-public-repo-template/actions/workflows/ci.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/python-fastapi-public-repo-template)](https://pypi.org/project/python-fastapi-public-repo-template/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1.0-6BA539)](docs/openapi.json)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)
[![Docker](https://img.shields.io/badge/container-Docker-2496ED)](Dockerfile)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/github/license/coldsofttech/python-fastapi-public-repo-template)](LICENSE)

A ready-to-use starting point for public HTTP APIs written in Python on GitHub. It includes a typed FastAPI service on top of a reusable library, a production-minded Docker image, automated testing on Python 3.11 to 3.15, linting, and the community and security files a public repository needs.

## What you get

- A FastAPI service with health and readiness probes, a versioned `/api/v1`, and interactive docs at `/docs`
- Three authentication modes you can switch on with one setting: none, API key and JWT
- Rate limiting, security headers, a request size limit and an option to hide the docs in production
- Consistent error responses, JSON logs and a request ID on every request
- A separate typed library, so your logic can be reused outside the API
- A small, non-root Docker image and a `compose.yaml` for running it locally
- A committed OpenAPI contract that CI keeps in sync with the code
- Optional publishing of the image to GHCR and of the package to PyPI, both off until you turn them on
- Fast, reproducible setup with [uv](https://docs.astral.sh/uv/)
- Linting, formatting and type checking before every commit and in CI
- Security scanning with CodeQL, Semgrep, Hadolint and Trivy, results in the Security tab
- API contract fuzzing with Schemathesis and breaking-change detection with oasdiff
- Automated tests on Python 3.11 to 3.15 (Ubuntu) and 3.11 (Windows and macOS)
- Contribution, conduct, support and security-reporting guidelines, issue forms and automated dependency updates

## Getting started

1. Click **Use this template** on GitHub and create your new repository.
2. Run the **Init** workflow from the Actions tab and merge the pull request it opens. This fills in your owner and repository name.
3. Rename the example library, the API package, the `example-api` command and the `EXAMPLE_API_` settings prefix. See the [development guide](docs/development.md).
4. Add your contact details in `CODE_OF_CONDUCT.md`, delete `.github/workflows/init.yml`, and replace this description.
5. Apply the repository protections by following the [setup guide](docs/repo-setup.md).
6. Install dependencies and commit checks:

   ```bash
   uv sync
   uv run pre-commit install --hook-type pre-commit --hook-type post-commit
   ```

## Running the API

```bash
uv run example-api
```

Then open <http://127.0.0.1:8000/docs>, or:

```console
$ curl http://127.0.0.1:8000/health
{"status":"ok"}
$ curl http://127.0.0.1:8000/api/v1/hello/Ada
{"message":"Hello, Ada!"}
```

With Docker:

```bash
docker compose up --build
```

Settings are read from `EXAMPLE_API_*` environment variables or a `.env` file (start from `.env.example`). See the [API reference](docs/api.md) for every endpoint, setting and authentication mode.

> After renaming the API, update the examples above. Once you have written your real endpoints, replace them with a short walkthrough.

## Development

```bash
git clone https://github.com/coldsofttech/python-fastapi-public-repo-template.git
cd python-fastapi-public-repo-template
uv sync
uv run pytest
```

See the [development guide](docs/development.md) for linting, type checking, Docker and releasing.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Please report security issues privately as described in [SECURITY.md](SECURITY.md).

## License

Released under the [MIT License](LICENSE).
