# Quick Start

Get FluxOmni running in minutes.

## Prerequisites

- `curl`
- `root` or `sudo` access on Debian/Ubuntu if Docker is not already installed

If Docker is already available, the installer uses it directly. Manual installs and non-Debian hosts still require Docker Engine with Docker Compose v2.

## One-line Install

```bash
curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash
```

By default, FluxOmni installs to `~/fluxomni` and follows the newest stable release channel (`latest`).
The installer creates a single-host compose stack with separate `control-plane` and `media-node` services that share `./data`.
The published `control-plane` image currently serves the operator UI directly, so the default release path does not require a separate frontend container.

## Install with Custom Values

This example opts into the `edge` channel and a custom install path:

```bash
FLUXOMNI_DIR=/opt/fluxomni \
FLUXOMNI_VERSION=edge \
  curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash
```

To pin a specific stable release instead, set `FLUXOMNI_VERSION=vX.Y.Z`.
To override the split image repositories directly, set `FLUXOMNI_CONTROL_PLANE_IMAGE` and `FLUXOMNI_MEDIA_NODE_IMAGE` before running the installer.

For pinned installs, the installer first tries the same self-host ref and falls back to `main` if versioned self-host assets are not published yet. Use `FLUXOMNI_SELFHOST_REF` only if the config bundle needs to come from a different ref.
Legacy automation that still exports `FLUXOMNI_IMAGE=<base-repository>` continues to work because the installer derives the split image names from that base when the explicit variables are unset.

## Attach Another Media Node

Run this on the remote media server:

```bash
FLUXOMNI_VERSION=edge \
FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT=http://control.example.com:50052 \
FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=replace-with-shared-token \
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=media2.example.com \
  curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash -s -- media-node
```

The media-node installer now defaults to `~/fluxomni-media-node`, writes a media-node-only compose bundle, verifies it can reach the control-plane RPC endpoint before startup, and only reports success after the local media-node confirms registration in its logs.
`FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` must be the real hostname or IP that should be advertised for that media server. In this example, the node joins `control.example.com` but advertises itself as `media2.example.com`.
If you want to advertise a different gRPC endpoint than `http://<media-node-public-host>:50051`, set `FLUXOMNI_MEDIA_NODE_ENDPOINT` explicitly before running the installer.
You can also set `FLUXOMNI_MEDIA_NODE_ID`, `FLUXOMNI_MEDIA_NODE_NAME`, `FLUXOMNI_MEDIA_NODE_LABELS`, and `FLUXOMNI_MEDIA_NODE_ZONE` when the default hostname-derived identity is not what you want.

## Access the Operator UI

After the containers are up, open `http://<your-server-ip>` in your browser.
Current releases use these primary operator surfaces:

- `/routes` for the route list
- `/routes/:id` for an individual route workspace
- `/fleet` for attached media-node inventory and health

## Manual Install

```bash
ASSET_REF=main # or a published versioned self-host ref, for example vX.Y.Z
mkdir -p ~/fluxomni
cd ~/fluxomni
curl -fsSL "https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/${ASSET_REF}/docker-compose.yml" -o docker-compose.yml
curl -fsSL "https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/${ASSET_REF}/.env.example" -o .env.example
AUTH_TOKEN="$(openssl rand -hex 24)"
IMAGE_TAG="${ASSET_REF}"
if [ "${IMAGE_TAG}" = "main" ]; then
  IMAGE_TAG="latest"
fi
cat > .env <<ENVVARS
FLUXOMNI_VERSION=${IMAGE_TAG}
FLUXOMNI_PUBLIC_HOST=127.0.0.1
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=127.0.0.1
FLUXOMNI_CONTROL_PLANE_IMAGE=ghcr.io/fluxomnia-systems/fluxomni-control-plane
FLUXOMNI_MEDIA_NODE_IMAGE=ghcr.io/fluxomnia-systems/fluxomni-media-node
FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=${AUTH_TOKEN}
FLUXOMNI_CONTROL_PLANE_HTTP_PORT=80
FLUXOMNI_MEDIA_NODE_RTMP_PORT=1935
FLUXOMNI_MEDIA_NODE_HLS_PORT=8000
FLUXOMNI_MEDIA_NODE_SRT_PORT=10080
FLUXOMNI_CONTROL_PLANE_DATA_DIR=./data
FLUXOMNI_MEDIA_NODE_DATA_DIR=./data
FLUXOMNI_SHARED_VIDEO_DIR=./data/videos
ENVVARS
mkdir -p data/videos data/dvr data/srs-http
touch data/state.json
docker compose up -d
```

Then open `http://<your-server-ip>/routes`.

## Next Steps

- Configure [authentication and settings](configuration.md)
- Review [cloud deployment guides](../deployment/)
- Use [troubleshooting](troubleshooting.md) if startup fails
