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

# Pin a specific release tag
FLUXOMNI_VERSION=vX.Y.Z \
  curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash

# Follow the latest mainline build instead of stable releases
FLUXOMNI_VERSION=edge \
  curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash
```

## What Gets Installed

- `docker-compose.yml`
- `.env` (created once, never overwritten automatically)
- `data/` with runtime state and recordings

Default install path: `~/fluxomni`

## Release Channels

- `latest` tracks the newest stable release and is the default for this repository.
- `vX.Y.Z` tags are immutable release images for a specific stable cut.
- `edge` tracks the latest successful publish from `main`.

Stable release notes are published on the [GitHub Releases](https://github.com/fluxomnia-systems/fluxomni/releases) page.

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
- [GitHub Releases](https://github.com/fluxomnia-systems/fluxomni/releases)
