# Fluxomni Studio Self-Hosted

<p align="center">
  <img src="docs/src/images/logo.webp" alt="Fluxomni Studio Logo" width="10%">
</p>

Fluxomni Studio runs live streams on your own server. Send one stream in. Fluxomni Studio can send it out to many places at once: RTMP, SRT, or Icecast.

This repo is for self-host installs. Linux and macOS are supported on x64 and ARM64. Windows is supported through WSL2 with Ubuntu.

## What's New in 2026.05.2

- **Stable public automation API** — GraphQL automation now uses Route and Artifacts vocabulary, release-pinned schema discovery at `/api/schema.graphql`, and a session-aware `@fluxomni/api-client`
- **Per-output origin audio control** — each destination can keep program audio, select a track or channel, or drop origin audio before mix-ins are applied
- **Configurable media baselines** — route workspaces can learn media profiles from real sources and reuse those baselines for playlist and source compatibility checks
- **More compact operator flows** — route workspaces, playlist controls, diagnostics, and route cards have tighter controls and clearer live-operation states

For older versions, see the [Release Channels](#release-channels) section below.

## Quick Install

```bash
curl -fsSL https://install.fluxomni.io | bash
```

After installation:

- open `http://<your-server-ip>`
- use `/routes` to manage streams
- use `/fleet` to check server health
- copy the RTMP publish address from a route workspace

> [!NOTE]
> On Debian and Ubuntu, the installer can install Docker automatically if it is missing. That path requires `root` or `sudo` access.

## Choose Your Setup

### Self-Hosted Stack

Best for most users. Installs Fluxomni Studio on one server.

```bash
curl -fsSL https://install.fluxomni.io | bash
```

### Standalone Media Node

Use this when Fluxomni Studio already runs somewhere else and this server should only move video.

```bash
FLUXOMNI_VERSION=edge \
FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT=http://control.example.com:50052 \
FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=replace-with-shared-token \
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=media2.example.com \
  curl -fsSL https://install.fluxomni.io | bash -s -- media-node
```

Set `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` to the real hostname or IP for this media server. Fluxomni Studio uses it for ingest and playback URLs.

## Common Install Examples

```bash
# Install into a custom directory
FLUXOMNI_DIR=/opt/fluxomni \
  curl -fsSL https://install.fluxomni.io | bash

# Pin a specific stable release
FLUXOMNI_VERSION=v2026.05.2 \
  curl -fsSL https://install.fluxomni.io | bash

# Use the newest main-branch build
FLUXOMNI_VERSION=edge \
  curl -fsSL https://install.fluxomni.io | bash

# Use a custom self-host config ref
FLUXOMNI_SELFHOST_REF=my-ref \
  curl -fsSL https://install.fluxomni.io | bash
```

## What the Installer Does

For the default self-host setup, the installer:

- installs Docker automatically on supported Debian and Ubuntu hosts if needed
- downloads the correct `docker-compose.yml` and `.env.example`
- creates or updates `.env` in place
- pulls and starts Fluxomni Studio
- preserves your existing `data/` directory on reruns
- verifies that the local services actually start before printing success

The web UI is included in the default install.

## Installed Files and Default Paths

| Install type | Default directory | Main services |
| --- | --- | --- |
| Self-hosted stack | `~/fluxomni` | Fluxomni Studio |
| Standalone media node | `~/fluxomni-media-node` | `media-node` |

The installer manages:

- `docker-compose.yml`
- `.env`
- `data/` for state, recordings, downloaded videos, and runtime files

## Release Channels

| Channel | Description |
| --- | --- |
| `latest` | Newest stable release (default) |
| `vYYYY.MM.N` | Public stable release tag |
| `vX.Y.Z` | Core image tag, accepted for direct image pinning |
| `edge` | Latest successful publish from `main` |

Use `latest` unless you need a pinned release or a test build. The current stable public release is `v2026.05.2`; it maps to core image tag `v0.13.0`.

See the What's New section above for the latest highlights.

## Manage Your Instance

If you used the default single-host install:

```bash
cd ~/fluxomni

# Troubleshooting (Connection & Health Doctor)
./doctor.sh

# Update to the currently configured image tags
docker compose pull
docker compose up -d

# Follow logs
docker compose logs -f

# Stop the stack
docker compose down
```

If you used a custom directory or installed only a media node, run these commands from that directory.

You can run `install.sh` again on the same install. It keeps your data and updates known `.env` keys.

## Advanced Installer Notes

- If `FLUXOMNI_VERSION` is pinned, the installer tries the matching self-host files first. Stable public pins fail loudly when matching assets are missing after release sync.
- Use `FLUXOMNI_SELFHOST_REF` to force a self-host asset ref.
- Use `FLUXOMNI_REPO_RAW` to use a custom raw asset base.
- Use `FLUXOMNI_FRONTEND_IMAGE`, `FLUXOMNI_CONTROL_PLANE_IMAGE`, and `FLUXOMNI_MEDIA_NODE_IMAGE` only when you publish your own images.

Useful standalone media-node overrides:

- `FLUXOMNI_MEDIA_NODE_ENDPOINT`
- `FLUXOMNI_MEDIA_NODE_ID`
- `FLUXOMNI_MEDIA_NODE_NAME`
- `FLUXOMNI_MEDIA_NODE_LABELS`
- `FLUXOMNI_MEDIA_NODE_ZONE`

## Documentation

Start here if you want step-by-step guidance:

- [Published documentation](https://docs.fluxomni.io/)
- [Book introduction](./docs/src/README.md)
- [Roadmap](./docs/src/roadmap.md)
- [Quick start](./docs/src/getting-started/quick-start.md)
- [Configuration](./docs/src/getting-started/configuration.md)
- [Private Access & Tunnels](./docs/src/getting-started/private-access.md)
- [Troubleshooting](./docs/src/getting-started/troubleshooting.md)
- [Deployment overview](./docs/src/deployment/overview.md)
- [Hetzner guide](./docs/src/deployment/hetzner.md)
- [DigitalOcean guide](./docs/src/deployment/digitalocean.md)
- [Oracle guide](./docs/src/deployment/oracle.md)
- [Vscale guide](./docs/src/deployment/vscale.md)

## Working on This Repository

This repository builds the published docs website from the `docs/` mdBook.

Before opening a PR that changes docs or the installer, run:

```bash
make lint
```

For the same strict check used in CI:

```bash
make lint.ci
```

Useful local commands:

- `make build` - build the docs into `docs/book`
- `make serve` - serve the docs locally
- `make lint` - build docs, check local Markdown links, and run markdownlint when available
- `make lint.ci` - strict CI docs lint; requires `markdownlint-cli2`
- `make screenshots` - refresh user-guide page and guided-flow screenshots from a running Fluxomni Studio instance

Compatibility aliases still exist for the older `make docs.build`, `make docs.serve`, `make docs.lint`, and `make docs.lint.ci` targets.

### User-Guide Screenshots

```bash
# Against a local Docker stack (default http://localhost)
make screenshots

# Against a specific host
FLUXOMNI_URL=http://192.168.1.100 make screenshots

# With auth enabled
FLUXOMNI_URL=http://192.168.1.100 FLUXOMNI_ADMIN_PASSWORD=secret make screenshots
```

See `screenshots/README.md` for the full image list and capture details.
