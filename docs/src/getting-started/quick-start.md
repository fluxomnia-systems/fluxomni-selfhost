# Quick Start

Get Fluxomni Studio running in minutes. Fluxomni Studio runs live streams on your own server. Send one stream in. Fluxomni Studio can send it out to many places at once: RTMP, SRT, or Icecast.

## Prerequisites

- **OS:** Linux or macOS with Docker. Windows works through WSL2 with Ubuntu.
- **Architecture:** x86_64 (x64) or ARM64 (AArch64).
- `curl`
- `root` or `sudo` access on Debian/Ubuntu if Docker is not already installed

If Docker is already installed, the installer uses it. Manual installs and non-Debian hosts need Docker Engine with Docker Compose v2.

## One-line Install

```bash
curl -fsSL https://install.fluxomni.io | bash
```

By default, Fluxomni Studio installs to `~/fluxomni` and follows the newest stable release channel (`latest`).
The installer creates one Docker Compose stack and stores data in `./data`.
The web UI is included in the default install.

## Install with Custom Values

This example uses the newest main-branch build and installs into `/opt/fluxomni`:

```bash
FLUXOMNI_DIR=/opt/fluxomni \
FLUXOMNI_VERSION=edge \
  curl -fsSL https://install.fluxomni.io | bash
```

To pin a stable release, set `FLUXOMNI_VERSION=v2026.05.1` or another public `vYYYY.MM.N` tag.

Use `FLUXOMNI_SELFHOST_REF` only when the config files must come from a different ref.

## Attach Another Media Node

Before attaching a remote media node, expose `50052/tcp` from the main
control-plane host only to trusted node IPs. For direct binding, set
`FLUXOMNI_CONTROL_PLANE_RPC_PORT=50052` in the main install's `.env`,
restart the stack, and restrict access with a firewall.

Run this on the remote media server:

```bash
FLUXOMNI_VERSION=edge \
FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT=http://control.example.com:50052 \
FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=replace-with-shared-token \
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=media2.example.com \
  curl -fsSL https://install.fluxomni.io | bash -s -- media-node
```

The installer writes files to `~/fluxomni-media-node`. It checks that it can reach the main Fluxomni Studio server before it starts.
Set `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` to the real hostname or IP for this media server.

Set `FLUXOMNI_MEDIA_NODE_ENDPOINT` only when the media server uses a custom gRPC endpoint.

You can also set `FLUXOMNI_MEDIA_NODE_ID`, `FLUXOMNI_MEDIA_NODE_NAME`, `FLUXOMNI_MEDIA_NODE_LABELS`, and `FLUXOMNI_MEDIA_NODE_ZONE`.

## Access the Operator UI

After Fluxomni Studio starts, open `http://<your-server-ip>`.
Current releases use these primary operator surfaces:

- `/routes` for the route list
- `/routes/:id` for an individual route workspace
- `/fleet` for server health

## Manual Install

```bash
ASSET_REF=main # or a published versioned self-host ref, for example v2026.05.1
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
FLUXOMNI_FRONTEND_IMAGE=ghcr.io/fluxomnia-systems/fluxomni-frontend
FLUXOMNI_CONTROL_PLANE_IMAGE=ghcr.io/fluxomnia-systems/fluxomni-control-plane
FLUXOMNI_MEDIA_NODE_IMAGE=ghcr.io/fluxomnia-systems/fluxomni-media-node
FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=${AUTH_TOKEN}
FLUXOMNI_FRONTEND_HTTP_PORT=80
FLUXOMNI_CONTROL_PLANE_RPC_PORT=127.0.0.1:50052
FLUXOMNI_MEDIA_NODE_RTMP_PORT=1935
FLUXOMNI_MEDIA_NODE_HLS_PORT=8000
FLUXOMNI_MEDIA_NODE_SRT_PORT=10080
FLUXOMNI_CONTROL_PLANE_DATA_DIR=./data
FLUXOMNI_MEDIA_NODE_DATA_DIR=./data
FLUXOMNI_SHARED_VIDEO_DIR=./data/videos
ENVVARS
mkdir -p data/videos data/dvr data/srs-http
touch data/state.db
docker compose up -d
```

Then open `http://<your-server-ip>/routes`.

## Auto-Updates

The compose stack includes a [Watchtower](https://containrrr.dev/watchtower/) service behind the `auto-update` profile. It is **not** started by default. To enable automatic daily image pulls and container recreation:

```bash
docker compose --profile auto-update up -d
```

To disable it again, stop the watchtower container:

```bash
docker compose --profile auto-update stop watchtower
```

## Next Steps

- Configure [authentication and settings](configuration.md)
- Use [private access and tunnels](private-access.md) for Tailscale or Cloudflare Tunnel deployments
- Review [cloud deployment guides](../deployment/)
- Use [troubleshooting](troubleshooting.md) if startup fails
