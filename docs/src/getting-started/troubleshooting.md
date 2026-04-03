# Troubleshooting

## Container Does Not Start

```bash
cd ~/fluxomni
docker compose logs -f control-plane media-node
```

For standalone remote media-node installs:

```bash
cd ~/fluxomni-media-node
docker compose logs -f media-node
```

Common causes:

- Docker daemon is not running.
- The selected image tag does not exist.
- `FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN` is missing from `.env` after a manual install.
- Port 80, 1935, 8000/tcp, 8000/udp, 10080/udp, 50051/tcp, or 50052/tcp is already in use.
- For standalone media-node installs, the control-plane RPC endpoint in `.env` is unreachable from the media server.
- For standalone media-node installs, the advertised `FLUXOMNI_MEDIA_NODE_ENDPOINT` does not point back to the media server.

## Media Node Does Not Appear in Fleet

If the control surface loads but a standalone node never shows up under `/fleet`, check the media-node logs:

```bash
cd ~/fluxomni-media-node
docker compose logs -f media-node
```

Look for a successful `Registered media node with control plane` message.
If it never appears, verify:

- `FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT` is reachable from the media-node host.
- `FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN` matches the control-plane value exactly.
- `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` and `FLUXOMNI_MEDIA_NODE_ENDPOINT` point back to the actual media-node host and published gRPC port.
- Any firewall between hosts allows TCP `50052` to the control-plane and the published media-node gRPC port back to the node when remote operators or services need it.

## Generated URLs Use the Wrong Hostname or IP

If the UI shows RTMP, HLS, SRT, or WebRTC URLs with a private IP, Docker hostname, or old domain, update these values in `.env` and restart the stack:

- `FLUXOMNI_PUBLIC_HOST` for control-plane links
- `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` for media ingest and playback links

On current releases, `/routes` is the main operator surface and `/fleet` shows attached media nodes. Those pages use the configured public hosts when they render copyable endpoints.

## Check Running State

```bash
cd ~/fluxomni
docker compose ps
```

Standalone media-node installs use the same command from `~/fluxomni-media-node`.

## Clean Restart

```bash
cd ~/fluxomni
docker compose down
docker compose up -d
```

## Rollback to a Previous Version

If an update causes issues, pin the previous version in `.env`:

```bash
cd ~/fluxomni
# Edit .env and change FLUXOMNI_VERSION to the previous release tag
sed -i 's/FLUXOMNI_VERSION=.*/FLUXOMNI_VERSION=v0.9.1/' .env
docker compose pull
docker compose up -d
```

Available release tags are listed on the [GitHub Releases](https://github.com/fluxomnia-systems/fluxomni/releases) page. Use `vX.Y.Z` format for immutable tags.

To return to tracking the latest stable release:

```bash
sed -i 's/FLUXOMNI_VERSION=.*/FLUXOMNI_VERSION=latest/' .env
docker compose pull
docker compose up -d
```
