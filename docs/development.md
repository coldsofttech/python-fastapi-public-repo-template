# Development

## Layout

```text
src/example_package/   library: all the logic, no web code (typed)
src/example_api/       FastAPI service: routers, schemas, auth, config, errors, logs
tests/                 pytest tests
pyproject.toml         metadata, dependencies and tool configuration
uv.lock                locked dependencies (commit this file)
```

The example names are `example_package` (library), `example_api` (API package), `example-api` (the command), the `EXAMPLE_API_` settings prefix and `example-api` (the Docker image tag used in CI). After creating a repo from this template:

1. Rename `src/example_package/` and `src/example_api/` to your import names, and update the imports in `src/`, `tests/` and `scripts/`.
2. In `pyproject.toml`, update `[tool.hatch.version]`, `[tool.hatch.build.targets.wheel]`, the `--cov=` options, and the command in `[project.scripts]`.
3. Change the `env_prefix` in `src/example_api/config.py`, then `.env.example`, `Dockerfile` (`EXAMPLE_API_HOST` and the `CMD`), and `docs/api.md`.
4. Update the API title in `src/example_api/main.py` and the image tag in `.github/workflows/ci.yml`.
5. Set the description in `pyproject.toml`, run `uv lock`, then regenerate the contract with `uv run python scripts/export_openapi.py`.

Endpoints, settings and authentication are documented in [API reference](api.md).

## Tooling

| Purpose | Tool |
| --- | --- |
| Environment, dependencies, build | [uv](https://docs.astral.sh/uv/) with Hatchling |
| Lint and format | Ruff |
| Type checking | mypy (strict) |
| Tests and coverage | pytest with pytest-cov (80% minimum) |

```bash
uv sync                    # create .venv and install dev dependencies
uv run pytest              # unit tests with coverage (skips integration tests)
uv run pytest -m integration --no-cov   # integration tests only
uv run ruff check .        # lint
uv run ruff format .       # format
uv run mypy                # type check
uv build                   # build sdist and wheel
uv run example-api         # run the server
uv run python scripts/export_openapi.py   # regenerate docs/openapi.json
docker compose up --build  # run in a container
```

## Integration tests

Tests under `tests/integration/` are marked `integration` automatically by that folder's `conftest.py`. They are excluded from the default `pytest` run, and therefore from the pre-commit hook, and run as their own job in CI. Put slower or end-to-end tests there.

## Continuous integration

The `ci` workflow runs five jobs: `lint` (pre-commit, including Ruff and mypy, plus a check that `docs/openapi.json` is up to date), `test` (unit tests), `integration` (tests marked `integration`, which start the real server), `docker` (builds the image and checks `/health` in a container) and `build` (build, `twine check` and a wheel import check). The `test` and `integration` jobs run on Python 3.11 to 3.15 on Ubuntu, and on 3.11 on Windows and macOS. A final `ci` job gates on all five and is the single required check in the branch ruleset.

## Releasing

Releases are triggered by publishing a GitHub release tagged `v<version>`. Publishing is off by default. Turn on the targets you want with repository variables (the settings script creates both set to `false`):

```bash
gh variable set PUBLISH_GHCR --body true   # Docker image to ghcr.io/<owner>/<repo>
gh variable set PUBLISH_PYPI --body true   # package to PyPI
```

1. Bump `__version__` in `src/<package>/__init__.py` and update `CHANGELOG.md`.
2. Publish a GitHub release tagged `v<version>`. The workflow fails if the tag and version differ.

**GHCR:** the image is tagged with the version, `major.minor` and `latest`, and a build provenance attestation is attached. Nothing else to set up. Make the package public in its settings if you want anyone to pull it.

**PyPI** uses [trusted publishing](https://docs.pypi.org/trusted-publishers/), so no API token is stored. Before the first release, add a trusted publisher on PyPI for this repository: workflow `release.yml`, environment `pypi`. The settings script creates the `pypi` environment and restricts it to `v*` tags.
