# FluxOmni Self-Hosted

Public installer and user documentation for running FluxOmni with prebuilt Docker images.

This repository intentionally does **not** include application source code.

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash
```

Useful overrides:

```bash
# Install into a custom directory
FLUXOMNI_DIR=/opt/fluxomni \
  curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash

# Pin a specific image tag
FLUXOMNI_VERSION=edge \
  curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash
```

## What Gets Installed

- `docker-compose.yml`
- `.env` (created once, never overwritten automatically)
- `data/` with runtime state and recordings

Default install path: `~/fluxomni`

## Manage Your Instance

```bash
cd ~/fluxomni

# Update
docker compose pull
docker compose up -d

# Logs
docker compose logs -f

# Stop
docker compose down
```

## Documentation

- [Book Introduction](./docs/src/README.md)
- [Quick Start](./docs/src/getting-started/quick-start.md)
- [Configuration](./docs/src/getting-started/configuration.md)
- [Troubleshooting](./docs/src/getting-started/troubleshooting.md)
- [Deployment Guides](./docs/src/deployment/)
