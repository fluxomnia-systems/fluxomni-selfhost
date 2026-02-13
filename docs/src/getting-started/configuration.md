# Configuration

FluxOmni is configured through environment variables in `.env`.

## Core Variables

- `FLUXOMNI_IMAGE`: Docker image repository.
- `FLUXOMNI_VERSION`: Image tag to deploy.
- `FLUXOMNI_PUBLIC_HOST`: Public hostname/IP shown in stream URLs.

Example:

```bash
FLUXOMNI_IMAGE=ghcr.io/fluxomnia-systems/fluxomni
FLUXOMNI_VERSION=edge
FLUXOMNI_PUBLIC_HOST=203.0.113.10
```

## Optional Variables

- `PASSWORD_HASH`: Argon2 hash for web UI authentication.
- `ALLOWED_IPS`: Comma-separated allowlist (`*` allows all).
- `FLUXOMNI_OTLP_COLLECTOR_IP`: OpenTelemetry collector host.
- `FLUXOMNI_OTLP_COLLECTOR_PORT`: OpenTelemetry collector port.
- `FLUXOMNI_SERVICE_NAME`: Service name for telemetry.

## Apply Changes

```bash
cd ~/fluxomni
docker compose up -d
```

## Update to Newest Image for Current Tag

```bash
cd ~/fluxomni
docker compose pull
docker compose up -d
```
