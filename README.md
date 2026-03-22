# FluxOmni Self-Hosted

Public installer and user documentation for running FluxOmni with prebuilt Docker images.

This repository intentionally does **not** include application source code.

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash
```

On Debian/Ubuntu hosts, this installer will bootstrap Docker automatically if it is missing. That path requires `root` or `sudo` access.
The installed stack now runs separate `control-plane` and `media-node` containers behind one single-host compose project.

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

# Override the published image repositories explicitly
FLUXOMNI_CONTROL_PLANE_IMAGE=registry.example.com/fluxomni-control-plane \
FLUXOMNI_MEDIA_NODE_IMAGE=registry.example.com/fluxomni-media-node \
  curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash
```

The installer still accepts legacy `FLUXOMNI_IMAGE=<base-repository>` overrides and derives `-control-plane` / `-media-node` image names from that base when the explicit split-image variables are unset.

When `FLUXOMNI_VERSION` is pinned, the installer first tries the same self-host ref. If that config bundle is not published yet, it falls back to `main` with a warning. Use `FLUXOMNI_SELFHOST_REF` to force a specific config bundle ref, or `FLUXOMNI_REPO_RAW` to point at a custom raw asset base.

## What Gets Installed

- `docker-compose.yml`
- `.env` (created once, never overwritten automatically)
- `data/` with shared single-host runtime state, downloaded videos, and recordings

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
docker compose logs -f control-plane media-node

# Stop
docker compose down
```

Re-running `install.sh` on an older single-container installation keeps the existing `./data` directory and appends any missing split-runtime variables to `.env`.

## Documentation

- [Book Introduction](./docs/src/README.md)
- [Quick Start](./docs/src/getting-started/quick-start.md)
- [Configuration](./docs/src/getting-started/configuration.md)
- [Troubleshooting](./docs/src/getting-started/troubleshooting.md)
- [Deployment Guides](./docs/src/deployment/)
- [GitHub Releases](https://github.com/fluxomnia-systems/fluxomni/releases)
