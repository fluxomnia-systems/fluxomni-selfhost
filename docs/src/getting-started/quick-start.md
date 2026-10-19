# Quick Start

Install Fluxomni Studio on your own server. Send one stream to several destinations at the same time using RTMP, SRT, or Icecast.

## Prerequisites

- **OS:** Linux or macOS with Docker. Windows works through WSL2 with Ubuntu.
- **Architecture:** x86_64 (x64) or ARM64 (AArch64).
- `curl`
- `root` or `sudo` access on Debian/Ubuntu if Docker is not already installed

If Docker is already installed, the installer uses it. Installer deployments require Docker Compose 2.20 or newer; manual installs need Docker Engine with Compose v2.

## One-line Install

```bash
curl -fsSL https://install.fluxomni.io | bash
```

By default, Fluxomni Studio installs to `~/fluxomni` and uses the newest stable release channel (`latest`).
The installer creates one Docker Compose stack and stores data in `./data`.
The web UI is included in the default install. The public launcher selects the stable release's matching installer and Compose assets, including its file-limit repair. Existing installs keep their saved version unless you set `FLUXOMNI_VERSION` explicitly. A saved `latest` continues following stable.

## Install with Custom Values

This example uses the newest main-branch build and installs into `/opt/fluxomni`:

```bash
curl -fsSL https://install.fluxomni.io | \
FLUXOMNI_DIR=/opt/fluxomni \
FLUXOMNI_VERSION=edge \
  bash
```

To pin a stable release, set `FLUXOMNI_VERSION=v26.3.2` or another public `vYY.Q.N` tag. The versioned URL `https://install.fluxomni.io/v26.3.2` also pins that release and uses the same corrected installer bundle. Older public aliases pass the mapped core image tag to historical installers.

Use `FLUXOMNI_SELFHOST_REF` only when the config files must come from a different ref.

## Attach Another Media Node

Use the procedure for the same release as your control plane. The `media-node` install target remains supported by the public command.

### Stable v26.3.2

The current stable release uses its published HTTP control and shared-token contract. Run this on the remote host after exposing the control listener only to trusted node IPs:

```bash
curl -fsSL https://install.fluxomni.io | \
FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT=http://control.example.com:50052 \
FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=replace-with-shared-token \
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=media2.example.com \
  bash -s -- media-node
```

The launcher selects the stable installer and assets together. The current v26.3.2 bundle is pinned to an immutable self-host snapshot that keeps the 65,536 file limit and published media-port fixes. For a pin, set the same published version as the control plane on the `bash` side of the pipe. Repeating that command uses the saved release and the same release's update behavior.

### Fleet enrollment on edge and supporting releases

Fleet enrollment requires matching control-plane and media-node images that support it. Until a supporting stable release is published, use `edge` for both and select `edge` in the Fleet join command. Existing stable credentials are not imported into the new control protocol. Use the documented [replacement procedure](capacity-upgrades.md) when moving an existing node.

Open Fleet → Add Node as an Admin. Choose the node ID and name, then select Generate join command. Copy the command and run it on the remote node host.

The command contains a fifteen-minute, single-use enrollment code. The installer creates and saves a machine credential before redeeming the code over verified HTTPS. The control plane stores its hash; the machine secret never passes through the browser.

The enrollment HTTPS origin and outbound control endpoint must be reachable from the node. Their certificates must match their hostnames. Fleet includes the control listener certificate as a pin. Advanced settings can use a stable issuing CA instead. Update the saved trust file when a pinned certificate is renewed. Use the separate enrollment HTTPS CA field for a private HTTPS origin.

A VPN, public node address and inbound node control port are optional. Leave the public host and HTTP relay host empty for a private node with no published ports. Configure media hosts only when publishers, viewers or HTTP relays need them.

Fleet distinguishes a consumed code from a connected node. After redemption, the existing outbound TLS handshake completes registration. Codes can be cancelled in Add Node, and expired codes can be replaced before successful enrollment.

The installer keeps credentials in owner-only `node-secrets/` under `~/fluxomni-media-node`. Repeating an interrupted installation reuses the saved secret. For a node that already started, follow [Capacity Ledger Upgrades](capacity-upgrades.md) before recreating it; maintenance reruns do not repeat enrollment.

## Access the Operator UI

After Fluxomni Studio starts, open `http://<your-server-ip>`.
Current releases use these main pages:

- `/routes` for the route list
- `/routes/:id` for an individual route workspace
- `/fleet` for server health

## Manual Install

```bash
ASSET_REF=v26.3.2 # Keep assets and images on the same published release.
mkdir -p ~/fluxomni
cd ~/fluxomni
curl -fsSL "https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/${ASSET_REF}/docker-compose.yml" -o docker-compose.yml
curl -fsSL "https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/${ASSET_REF}/.env.example" -o .env.example
AUTH_TOKEN="$(openssl rand -hex 24)"
IMAGE_TAG="${ASSET_REF}"
if [ "${IMAGE_TAG}" = "main" ]; then
  IMAGE_TAG="edge"
elif [[ "${IMAGE_TAG#v}" =~ ^[0-9]{2}\.[1-4]\.[0-9]+$ ]]; then
  VERSION_MAP="$(mktemp)"
  curl -fsSL "https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/${ASSET_REF}/scripts/generated-version-map.sh" -o "${VERSION_MAP}"
  . "${VERSION_MAP}"
  RESOLVED_IMAGE_TAG="$(generated_public_release_alias "${IMAGE_TAG}" 2>/dev/null || true)"
  rm -f "${VERSION_MAP}"
  if [ -n "${RESOLVED_IMAGE_TAG}" ]; then
    IMAGE_TAG="${RESOLVED_IMAGE_TAG}"
  fi
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

Keep automatic updates disabled for capacity-ledger builds. Watchtower cannot coordinate the cluster drain and shutdown proofs required before container recreation. For existing installations, use [Capacity Ledger Upgrades](capacity-upgrades.md).

To stop an updater enabled by an earlier deployment:

```bash
docker compose --profile auto-update stop watchtower
```

## Next Steps

- Complete [First Stream](first-stream.md) to create an account, publish a route, add an output, and verify playback
- Configure [authentication and settings](../user-guide/settings.md)
- Use [private access and tunnels](private-access.md) for Tailscale or Cloudflare Tunnel deployments
- Review [cloud deployment guides](../deployment/)
- Use [troubleshooting](troubleshooting.md) if startup fails

For per-node playlist normalization CPU/memory/thread budgets, see
[Offline Preparation Resource Limits](configuration.md#offline-preparation-resource-limits).

If redemption loses its response, the installer keeps the same credential and confirms it through the outbound control connection. Rerun the original command after an interrupted install. Never delete `node-secrets/` to retry.

## Legacy shared-token nodes

Legacy shared-token nodes require replacement enrollment; the installer does not import shared tokens or retain the old HTTP control protocol.

Drain legacy routes and prove predecessor execution stopped through [Capacity Ledger Upgrades](capacity-upgrades.md). Preserve the existing data, ownership ledger and configuration. With the current control plane running, create a fresh node ID in Fleet and run its join command with `FLUXOMNI_DIR` set to a new installation directory. Verify the new node before enabling routes. The in-place node upgrade command applies to installations that already have `node-secrets/`.

## Changing the control certificate host

An existing certificate must cover the advertised control host. Bootstrap rejects a missing name while preserving the existing certificate and key.

Through the capacity maintenance procedure, stop execution, preserve the old certificate and key, install the replacement covering the control host and update every node trust file. Restart and verify Fleet before enabling routes. A stable issuing CA avoids replacing the trust anchor at each certificate renewal.

Bootstrap also requires an explicit trust transition for expiring or incomplete certificate/key pairs. It preserves existing files and node trust instead of silently creating a new pin.
