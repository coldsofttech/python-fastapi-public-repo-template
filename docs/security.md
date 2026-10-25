# Security

What the template protects against out of the box, what it leaves to your infrastructure, and how issues are found.

## Built into the app

| Protection | How | Setting |
| --- | --- | --- |
| Authentication | API key or JWT on protected routes ([details](api.md)) | `EXAMPLE_API_AUTH_MODE` |
| Rate limiting | Fixed window per client address, `429` with `Retry-After` and `X-RateLimit-*` headers. Health probes are exempt. | `EXAMPLE_API_RATE_LIMIT_PER_MINUTE` (default 120, `0` turns it off) |
| Request size limit | `413` when the declared `Content-Length` is too large | `EXAMPLE_API_MAX_BODY_BYTES` (default 1 MiB) |
| Security headers | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, a strict `Content-Security-Policy` (except on the docs pages), `Cache-Control: no-store` on `/api/`, and HSTS over HTTPS | none |
| Host allow-list | Rejects unknown `Host` headers | `EXAMPLE_API_ALLOWED_HOSTS` |
| CORS | Off until you list origins; only `GET` and the auth headers | `EXAMPLE_API_CORS_ORIGINS` |
| Docs exposure | `/docs`, `/redoc` and `/openapi.json` can be switched off. The Docker image turns them off; `compose.yaml` turns them back on for local use. | `EXAMPLE_API_DOCS_ENABLED` |
| Safe errors | Problem details responses; 500 errors never expose details or stack traces | none |
| Secrets | Held as `SecretStr`, never logged, constant-time comparison for API keys | none |
| Container | Non-root user, slim base image, no build tools in the final image | none |

Rate limiting counts in memory, so each instance enforces its own limit. For an exact global limit, enforce it at the proxy or gateway, or back `RateLimiter` with a shared store such as Redis. Behind a proxy, set `EXAMPLE_API_FORWARDED_ALLOW_IPS` so the limiter sees real client addresses (see [deployment](deployment.md)).

## Left to your infrastructure

HTTPS and certificates, request timeouts, connection limits, a web application firewall, and request size limits for chunked uploads belong to the reverse proxy or load balancer.

## Automated checks

| Check | Where | What it finds |
| --- | --- | --- |
| Ruff `S` rules | pre-commit and `ci` | Insecure Python patterns (Bandit rules) |
| gitleaks | pre-commit and `ci` | Committed secrets |
| CodeQL | GitHub default setup | Code vulnerabilities |
| Dependency review | `dependency-review.yml` | Vulnerable dependencies added by a pull request |
| pip-audit | `audit.yml`, weekly | Advisories published against locked dependencies |
| Semgrep | `security.yml` | Python, OWASP Top 10, Dockerfile and workflow issues |
| Hadolint | `security.yml` | Dockerfile mistakes and bad practices |
| Trivy | `security.yml` | Known vulnerabilities (high and critical) in the built image |
| Schemathesis | `tests/integration` | Server errors for any request the OpenAPI document allows |
| oasdiff | `api-compat.yml` | Changes that break existing API callers |

The `security.yml` jobs upload SARIF, so results appear under **Security > Code scanning** on GitHub, and they run on pull requests, on pushes to `main` and weekly. They are not part of the required `ci` check, so a newly published advisory does not block unrelated work. To make one required, add its job name to the branch ruleset.

To suppress a false positive, prefer a narrow, commented exception: `# nosemgrep: <rule-id>` for Semgrep, a `.trivyignore` entry with a reason for Trivy, or `# hadolint ignore=DLxxxx` for Hadolint.

## Reporting a vulnerability

See [SECURITY.md](../SECURITY.md).
