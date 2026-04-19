# Troubleshooting

## Installation Health Check (Doctor)

If you encounter issues during or after installation, run the diagnostic script from your install directory:

```bash
# From your install directory (default ~/fluxomni)
./doctor.sh
```

The script verifies:

- Docker and Docker Compose installation
- Environment configuration (`.env`)
- Port availability (checks for conflicts with other services)
- Container running status
- Disk space and data directory integrity

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

## Port Already in Use

If Docker fails with an error like:

```text
failed to bind port 0.0.0.0:80/tcp: Error starting userland proxy: listen tcp4 0.0.0.0:80: bind: address already in use
```

Another service on the host is already listening on that port. This is common on NAS devices (Synology, QNAP, Unraid) where the built-in web UI occupies port 80. Port 8000 (HLS/WebRTC) is another frequent conflict — Synology DSM uses it as an alternative HTTP port, and media apps like Plex or Jellyfin may also bind to it.

**Fix:** override the conflicting host ports in `.env` without editing `docker-compose.yml`:

```bash
# Change the Control Surface port from 80 to 8080
echo 'FLUXOMNI_CONTROL_PLANE_HTTP_PORT=8080' >> .env

# Change HLS/WebRTC port from 8000 to 8800 (if 8000 is also taken)
echo 'FLUXOMNI_MEDIA_NODE_HLS_PORT=8800' >> .env
```

Then restart the stack:

```bash
docker compose down
docker compose up -d
```

Access the Control Surface at `http://<HOST-IP>:8080`. If you also set `FLUXOMNI_PUBLIC_URL`, make sure it includes the new port (e.g. `http://nas.local:8080`).

## Multi-Subnet and NAT Environments

In environments with multiple networks (e.g. cloud VPCs, complex office LANs, or behind NAT), the Web UI might be unreachable if the public-facing address is misconfigured.

The **Self-Host Doctor** (`./doctor.sh`) will automatically detect your local IP addresses and warn you if `FLUXOMNI_PUBLIC_HOST` is set to a restricted loopback address.

**Symptoms:**

- Browser shows "Connection Timed Out" or "Connection Refused".
- The doctor script warns that `FLUXOMNI_PUBLIC_HOST` does not match any local IP.

**Resolution:**

1. **Run the Doctor:** `./doctor.sh` to see the recommended IPs for your host.
2. **Set the correct Public Host:** ensure `FLUXOMNI_PUBLIC_HOST` in `.env` is set to the IP or hostname that your **browser** uses to reach the server.
3. **Bind to all interfaces:** if you want the Control Plane to be reachable from any network connected to the server, ensure `FLUXOMNI_CONTROL_PLANE_HTTP_BIND` is set to `0.0.0.0:<port>` (default in most setups).
4. **Check NAT Reflection:** if you are accessing the server via a public IP from inside the same LAN, ensure your router supports NAT reflection (Hairpin NAT).

If you are using a reverse proxy (Nginx, Traefik, Caddy), set `FLUXOMNI_PUBLIC_URL` to the full proxy URL:

```bash
FLUXOMNI_PUBLIC_URL=https://fluxomni.example.com
```

All port mappings in `docker-compose.yml` support the same pattern — override via the corresponding `FLUXOMNI_*` variable in `.env`:

| Variable | Default | Service |
| -------- | ------- | ------- |
| `FLUXOMNI_CONTROL_PLANE_HTTP_PORT` | 80 | Control Surface (HTTP) |
| `FLUXOMNI_CONTROL_PLANE_RPC_PORT` | 50052 | Control-plane gRPC |
| `FLUXOMNI_MEDIA_NODE_RTMP_PORT` | 1935 | RTMP ingest |
| `FLUXOMNI_MEDIA_NODE_HLS_PORT` | 8000 | HLS and WebRTC |
| `FLUXOMNI_MEDIA_NODE_SRT_PORT` | 10080 | SRT ingest |

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
- If you forgot the admin password, current installs store user accounts in `data/state.db`, not `data/state.json`. Stop the stack first, back up `data/`, and use `sqlite3 data/state.db` as a last-resort recovery path if you need to inspect or repair the `users` table before restarting.
- If no user accounts exist, FluxOmni falls back to the open admin shell. After emergency recovery, use Settings to create a new admin account before re-enabling named-user sign-in.

## Rollback to a Previous Version

If an update causes issues, pin the previous version in `.env`:

```bash
# From your install directory
# Edit .env and change FLUXOMNI_VERSION to the previous release tag
sed -i 's/FLUXOMNI_VERSION=.*/FLUXOMNI_VERSION=v0.10.1/' .env
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
