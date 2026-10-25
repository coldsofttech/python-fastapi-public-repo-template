# Deployment

The app listens on a host and port. Your domain name, DNS records and HTTPS certificates are set up in front of it, by a reverse proxy, load balancer or platform ingress. This page shows how the pieces fit.

## Where each thing is configured

| What | Where |
| --- | --- |
| Domain name and DNS | Your DNS provider, pointing at the proxy or load balancer |
| HTTPS certificate | The proxy or load balancer (for example Caddy, nginx, Traefik or a cloud load balancer) |
| Port the app listens on | `EXAMPLE_API_PORT` (default `8000`) |
| Interface the app listens on | `EXAMPLE_API_HOST` (`127.0.0.1` by default, `0.0.0.0` in the Docker image) |
| Port exposed to the outside | The Docker port mapping in `compose.yaml`, or your platform's service definition |
| Accepted domains | `EXAMPLE_API_ALLOWED_HOSTS` |
| Browser origins allowed to call the API | `EXAMPLE_API_CORS_ORIGINS` |

## Behind a reverse proxy

A typical setup is `client -> proxy (HTTPS, your domain) -> app (plain HTTP, private network)`.

1. Run the app on a private address and keep it unreachable except through the proxy.
2. Set `EXAMPLE_API_FORWARDED_ALLOW_IPS` to the proxy's address, so the app trusts its `X-Forwarded-For` and `X-Forwarded-Proto` headers. Without this the app sees the proxy's IP and `http` instead of the real client and `https`. Never trust forwarded headers from addresses you do not control.
3. Set `EXAMPLE_API_ALLOWED_HOSTS` to your domain, for example `["api.example.com"]`. Requests with any other `Host` header get a 400.
4. Include `127.0.0.1` in `EXAMPLE_API_ALLOWED_HOSTS` when you set it, because the Docker health check and local probes use that host.

Example Caddyfile (Caddy gets and renews the certificate for you):

```text
api.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

## Serving under a sub-path

If the proxy exposes the API at `https://example.com/myapi/` and strips the prefix before forwarding, set `EXAMPLE_API_ROOT_PATH=/myapi`. The docs page and the OpenAPI document then use the right URLs.

## Health probes

Point your platform at the two probes:

| Probe | Path | Meaning |
| --- | --- | --- |
| Liveness | `/health` | The process is running. Restart the container if it fails. |
| Readiness | `/ready` | The service can take traffic. Add checks for your dependencies in `routers/health.py`. |

The Docker image already has a health check that follows `EXAMPLE_API_PORT`.

## Scaling and shutdown

Run more containers behind the load balancer instead of more workers inside one container. The app keeps no shared state, so any instance can answer any request. If you do run several processes in one container, set `EXAMPLE_API_WORKERS`.

Rate limits are counted per process, so with many instances the effective limit is the per-instance limit times the number of instances. Enforce an exact global limit at the proxy or gateway.

On shutdown the server stops accepting connections and gives in-flight requests `EXAMPLE_API_SHUTDOWN_TIMEOUT` seconds (default 10) to finish. Keep your platform's termination grace period longer than that.

## Hiding the interactive docs

The Docker image sets `EXAMPLE_API_DOCS_ENABLED=false`, which removes `/docs`, `/redoc` and `/openapi.json`. Set it to `true` for an internal API or while developing. The committed `docs/openapi.json` is unaffected.

## Not covered by the app

HTTPS and certificates, request timeouts, connection limits, a web application firewall, and size limits for chunked uploads are best handled by the proxy or load balancer. See [security](security.md) for what the app itself enforces.
