# FluxOmni Self-Hosted

<p align="center">
  <img src="docs/src/images/logo.webp" alt="FluxOmni Logo" width="10%">
</p>

Install FluxOmni — a multi-protocol live streaming platform — on your own *nix server (x64 or ARM64) with a single command. Windows is not supported natively; WSL2 may work but is untested and unsupported.

FluxOmni lets you broadcast from a single source (RTMP, SRT, or WebRTC) to multiple destinations (RTMP, SRT, Icecast) simultaneously. It uses a split runtime made of a `control-plane` and a `media-node`. The default installer runs both on the same host, so most users can get started quickly without learning the multi-host layout first.

## What's New in 0.10.1

- **Stable push token rotation** — rotate publish credentials without recreating the route
- **Simplified Fleet onboarding** — streamlined Add Node flow, clean node removal, and full proxy URL support
- **Immutable main build tags** — pin a known `main-<shortsha>` image without rebuilding
- **Smarter cold-start probes** — ffprobe timeouts no longer leak false errors to the operator UI

For older versions, see the [Release Channels](#release-channels) section below.

## Quick Install

```bash
curl -fsSL https://install.fluxomni.io | bash
```

After installation:

- open `http://<your-server-ip>` in your browser
- manage routes at `/routes`
- inspect node health at `/fleet`
- publish to the RTMP address shown in the route workspace

> [!NOTE]
> On Debian and Ubuntu, the installer can install Docker automatically if it is missing. That path requires `root` or `sudo` access.

## Choose Your Setup

### Single Host Stack

Best for most users. Runs the `control-plane` and `media-node` on one server.

```bash
curl -fsSL https://install.fluxomni.io | bash
```

### Standalone Media Node

Use this when you already have a control-plane and want to add another remote media node.

```bash
FLUXOMNI_VERSION=edge \
FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT=http://control.example.com:50052 \
FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=replace-with-shared-token \
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=media2.example.com \
  curl -fsSL https://install.fluxomni.io | bash -s -- media-node
```

Standalone media-node installs require `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` because FluxOmni uses that host when it advertises ingest and playback URLs and when it derives the default media-node gRPC endpoint.

## Common Install Examples

```bash
# Install into a custom directory
FLUXOMNI_DIR=/opt/fluxomni \
  curl -fsSL https://install.fluxomni.io | bash

# Pin a specific stable release
FLUXOMNI_VERSION=vX.Y.Z \
  curl -fsSL https://install.fluxomni.io | bash

# Follow the latest mainline publish instead of stable releases
FLUXOMNI_VERSION=edge \
  curl -fsSL https://install.fluxomni.io | bash

# Override the published image repositories explicitly
FLUXOMNI_CONTROL_PLANE_IMAGE=registry.example.com/fluxomni-control-plane \
FLUXOMNI_MEDIA_NODE_IMAGE=registry.example.com/fluxomni-media-node \
  curl -fsSL https://install.fluxomni.io | bash
```

## What the Installer Does

For the default single-host setup, the installer:

- installs Docker automatically on supported Debian and Ubuntu hosts if needed
- downloads the correct `docker-compose.yml` and `.env.example`
- creates or updates `.env` in place
- pulls and starts the published FluxOmni containers
- preserves your existing `data/` directory on reruns
- verifies that the local services actually start before printing success

Current self-host releases use the split runtime directly, and the published `control-plane` image currently embeds the operator UI, so no separate frontend image is required in the default release path.

## Installed Files and Default Paths

| Install type | Default directory | Main services |
| --- | --- | --- |
| Single host | `~/fluxomni` | `control-plane`, `media-node` |
| Standalone media node | `~/fluxomni-media-node` | `media-node` |

The installer manages:

- `docker-compose.yml`
- `.env`
- `data/` for state, recordings, downloaded videos, and runtime files

## Release Channels

| Channel | Description |
| --- | --- |
| `latest` | Newest stable release (default) |
| `vX.Y.Z` | Immutable stable release tag |
| `edge` | Latest successful publish from `main` |

Published self-host releases use:

- `ghcr.io/fluxomnia-systems/fluxomni-control-plane`
- `ghcr.io/fluxomnia-systems/fluxomni-media-node`

Use the `latest`, `edge`, and `vX.Y.Z` channels above to control which published build gets installed.

See the [What's New](#whats-new-in-0101) section for the latest highlights.

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
docker compose logs -f control-plane media-node

# Stop the stack
docker compose down
```

If you installed into a custom directory, or deployed a standalone media node, use that directory instead.

Re-running `install.sh` on an existing install keeps the managed data directory and updates known `.env` keys in place. That makes it safe to repair ports, image tags, install target, or node settings without rewriting the whole file by hand.

## Advanced Installer Notes

- Legacy `FLUXOMNI_IMAGE=<base-repository>` is still supported. When the explicit split-image variables are unset, the installer derives `-control-plane` and `-media-node` image names from that base repository.
- When `FLUXOMNI_VERSION` is pinned, the installer first tries the matching self-host asset ref. If that config bundle is not published yet, it falls back to `main` with a warning.
- Use `FLUXOMNI_SELFHOST_REF` to force a specific self-host asset ref.
- Use `FLUXOMNI_REPO_RAW` to point the installer at a custom raw asset base.

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
- [Quick start](./docs/src/getting-started/quick-start.md)
- [Configuration](./docs/src/getting-started/configuration.md)
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
- `make screenshots` - refresh user-guide page and guided-flow screenshots from a running FluxOmni instance

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
