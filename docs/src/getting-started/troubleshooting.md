# Troubleshooting

## Container Does Not Start

Navigate to your FluxOmni install directory and check the logs:

```bash
# Default: ~/fluxomni
cd ~/fluxomni
docker compose logs -f control-plane media-node
```

For standalone remote media-node installs:

```bash
# Default: ~/fluxomni-media-node
cd ~/fluxomni-media-node
docker compose logs -f media-node
```

Common causes:

- Docker daemon is not running.
- The selected image tag does not exist.
- `FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN` is missing from `.env` after a manual install.
- Port 80, 1935, 8000/tcp, 8000/udp, 8081/tcp (loopback), 10080/udp, 50051/tcp, or 50052/tcp is already in use.
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

From your install directory:

```bash
docker compose ps
```

## Clean Restart

From your install directory:

```bash
docker compose down
docker compose up -d
```

## Playlist File Errors

Files in a route playlist show a signal integrity badge:

- **REF** — the file matches the reference stream parameters. No issues.
- **DIFF** — the file has different codec, resolution, or frame rate than the reference. This may cause brief glitches or quality changes during playback transitions.
- **ERROR** — the file could not be probed. It may be corrupt, still downloading, or in an unsupported format.

To fix DIFF warnings, re-encode files to match the reference parameters shown in the playlist status bar (codec, resolution, frame rate, audio channels).

## Disk Space

If the control-plane or media-node containers exit unexpectedly, check available disk space:

```bash
df -h ~/fluxomni/data
```

Playlist file downloads and DVR recordings can fill the disk. Free space by:

- Clearing unused playlist files from route playlists.
- Removing old DVR segments from `data/dvr/`.
- Moving the data directory to a larger volume and updating `FLUXOMNI_CONTROL_PLANE_DATA_DIR` and `FLUXOMNI_MEDIA_NODE_DATA_DIR` in `.env`.

## Firewall and Port Issues

FluxOmni uses both TCP and UDP ports. A common mistake is only opening TCP:

| Port | Protocol | Service |
| ---- | -------- | ------- |
| 80 | TCP | Control Surface (HTTP) |
| 1935 | TCP | RTMP ingest |
| 8000 | TCP + UDP | HLS and WebRTC |
| 8081 | TCP (localhost) | SRS callback (internal) |
| 10080 | UDP | SRT ingest |
| 50051 | TCP | Media-node gRPC |
| 50052 | TCP | Control-plane gRPC |

SRT (port 10080) is **UDP only**. If SRT publishers cannot connect, verify that UDP traffic is allowed through your firewall or cloud security group.

HLS and WebRTC (port 8000) require **both TCP and UDP**. WebRTC uses UDP for media transport.

## Stream Quality Issues

If the output stream has artifacts, stuttering, or audio sync problems:

- Check the **Signal Integrity** panel on the routes list for mismatch or fetch warnings.
- Open the route workspace and verify the input codec info matches what your encoder is sending.
- Ensure your encoder bitrate does not exceed the server's upload bandwidth.
- For playlist playback, verify all files use the same codec, resolution, and frame rate as the primary source.

## Cannot Sign In

If you are locked out of the Control Surface:

- Verify the username and password. Passwords are case-sensitive.
- If you forgot the admin password, stop the stack and edit `data/state.json` to reset the auth configuration. Then restart and set a new password from the Settings page.
- If the sign-in mode is set to "Named user sign-in" but no user accounts exist, the Control Surface shows the authentication screen. You may need to reset state to recover access.

## Rollback to a Previous Version

If an update causes issues, pin the previous version in `.env`:

```bash
# From your install directory
# Edit .env and change FLUXOMNI_VERSION to the previous release tag
sed -i 's/FLUXOMNI_VERSION=.*/FLUXOMNI_VERSION=v0.9.1/' .env
docker compose pull
docker compose up -d
```

Available release tags are listed on the [GitHub Releases](https://github.com/fluxomnia-systems/fluxomni/releases) page. Use `vX.Y.Z` format for immutable tags.

To return to tracking the latest stable release, from the same directory:

```bash
sed -i 's/FLUXOMNI_VERSION=.*/FLUXOMNI_VERSION=latest/' .env
docker compose pull
docker compose up -d
```
