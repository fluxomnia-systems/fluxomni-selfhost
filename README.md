# FluxOmni Self-Hosted

Public installer and user documentation for running FluxOmni with prebuilt Docker images.
FluxOmni lets you stream to multiple platforms simultaneously with a split `control-plane` + `media-node` runtime, even on a single host.

This repository intentionally does **not** include application source code.

## Quick Install

```bash
curl -fsSL https://install.fluxomni.io | bash
```

On Debian/Ubuntu hosts, this installer will bootstrap Docker automatically if it is missing. That path requires `root` or `sudo` access.
The installed stack now runs separate `control-plane` and `media-node` containers behind one single-host compose project.
Published self-host releases use the split runtime directly, and the published `control-plane` image currently embeds the operator UI so no separate frontend image is required on the default release path.

Useful overrides:

```bash
# Install into a custom directory
FLUXOMNI_DIR=/opt/fluxomni \
  curl -fsSL https://install.fluxomni.io | bash

# Pin a specific release tag
FLUXOMNI_VERSION=vX.Y.Z \
  curl -fsSL https://install.fluxomni.io | bash

# Follow the latest mainline build instead of stable releases
FLUXOMNI_VERSION=edge \
  curl -fsSL https://install.fluxomni.io | bash

# Install only a standalone media-node for an existing control-plane.
# The positional `media-node` target is safer than relying on env-only mode.
FLUXOMNI_VERSION=edge \
FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT=http://control.example.com:50052 \
FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=replace-with-shared-token \
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=media2.example.com \
  curl -fsSL https://install.fluxomni.io | bash -s -- media-node

# Override the published image repositories explicitly
FLUXOMNI_CONTROL_PLANE_IMAGE=registry.example.com/fluxomni-control-plane \
FLUXOMNI_MEDIA_NODE_IMAGE=registry.example.com/fluxomni-media-node \
  curl -fsSL https://install.fluxomni.io | bash
```

The installer still accepts legacy `FLUXOMNI_IMAGE=<base-repository>` overrides and derives `-control-plane` / `-media-node` image names from that base when the explicit split-image variables are unset.

When `FLUXOMNI_VERSION` is pinned, the installer first tries the same self-host ref. If that config bundle is not published yet, it falls back to `main` with a warning. Use `FLUXOMNI_SELFHOST_REF` to force a specific config bundle ref, or `FLUXOMNI_REPO_RAW` to point at a custom raw asset base.

After installation, open `http://<your-server-ip>` in a browser. Current releases use:

- `/routes` for the route list
- `/routes/:id` for an individual route workspace
- `/fleet` for attached media-node inventory and health

## What Gets Installed

- `docker-compose.yml`
- `.env` (created if missing and updated in place on reruns)
- `data/` with shared single-host runtime state, downloaded videos, and recordings

Default install path: `~/fluxomni`
For `media-node` installs, the default path is `~/fluxomni-media-node`, and `docker-compose.yml` contains only the standalone `media-node` service plus watchtower.

## Release Channels

- `latest` tracks the newest stable release and is the default for this repository.
- `vX.Y.Z` tags are immutable release images for a specific stable cut.
- `edge` tracks the latest successful publish from `main`.

Published releases promote the split `fluxomni-control-plane` and `fluxomni-media-node` images directly.

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

Re-running `install.sh` on an older installation keeps the existing `./data` directory and updates the managed `.env` keys in place so incorrect ports, targets, and node settings can be repaired without a manual rewrite.
Media-node installs now verify control-plane reachability before startup and only print success after the local node logs confirm registration with the control-plane.
`FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` is required for standalone media-node installs because FluxOmni uses that host when it advertises ingest/playback URLs and when it derives the default media-node gRPC endpoint.

Useful standalone media-node overrides:

- `FLUXOMNI_MEDIA_NODE_ENDPOINT` when the advertised gRPC address should differ from `http://<FLUXOMNI_MEDIA_NODE_PUBLIC_HOST>:50051`
- `FLUXOMNI_MEDIA_NODE_ID` when the hostname-derived node ID is not what you want
- `FLUXOMNI_MEDIA_NODE_NAME` when you want a custom display name in the control-plane
- `FLUXOMNI_MEDIA_NODE_LABELS` for capability or grouping labels
- `FLUXOMNI_MEDIA_NODE_ZONE` for placement/location metadata

## Documentation

- [Book Introduction](./docs/src/README.md)
- [Quick Start](./docs/src/getting-started/quick-start.md)
- [Configuration](./docs/src/getting-started/configuration.md)
- [Troubleshooting](./docs/src/getting-started/troubleshooting.md)
- [Deployment Guides](./docs/src/deployment/)
- [Published docs website](https://docs.fluxomni.io/)
- [GitHub Releases](https://github.com/fluxomnia-systems/fluxomni/releases)

## Docs Development

The published docs website is built from the `docs/` mdBook in this repository.
Before opening a PR that changes the docs website, run:

```bash
make lint
```

For the same strict check used in CI, run:

```bash
make lint.ci
```

Useful local docs commands:

- `make build` — build the published docs site into `docs/book`
- `make serve` — serve the site locally
- `make lint` — build docs, check local Markdown links, and run markdownlint when installed
- `make lint.ci` — strict CI docs lint; requires `markdownlint-cli2`

The older `make docs.build`, `make docs.serve`, `make docs.lint`, and `make docs.lint.ci` targets remain available as compatibility aliases.
