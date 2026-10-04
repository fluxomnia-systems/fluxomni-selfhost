# Configuration

Fluxomni Studio is configured through environment variables in `.env`.

## Core Variables

- `FLUXOMNI_FRONTEND_IMAGE`: frontend image repository.
- `FLUXOMNI_CONTROL_PLANE_IMAGE`: control-plane image repository.
- `FLUXOMNI_MEDIA_NODE_IMAGE`: media-node image repository.
- `FLUXOMNI_VERSION`: image tag to deploy.
- `FLUXOMNI_PUBLIC_HOST`: public hostname/IP used for the control surface and generated control-plane URLs.
- `FLUXOMNI_PUBLIC_URL`: full public base URL including scheme (e.g. `https://stream.example.com`). Required for HTTPS deployments behind a TLS-terminating reverse proxy. Takes precedence over `FLUXOMNI_PUBLIC_HOST` + `FLUXOMNI_FRONTEND_HTTP_PORT`.
- `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST`: public hostname/IP shown in generated RTMP, HLS, SRT, and WebRTC media URLs.
- `FLUXOMNI_MEDIA_NODE_ID`: stable media-node identifier shown in fleet views.
- `FLUXOMNI_MEDIA_NODE_NAME`: human-readable media-node name shown in the control-plane.
- `FLUXOMNI_MEDIA_NODE_LABELS`: optional comma-separated capability labels for routing and fleet filters.
- `FLUXOMNI_MEDIA_NODE_ZONE`: optional placement zone used to describe where the node runs.

`FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` is especially important for standalone media-node installs.
Fluxomni Studio uses it in two places:

- It is shown in the RTMP, HLS, SRT, and WebRTC URLs that operators and publishers use.
- For standalone media-node installs, it is used to derive the default `FLUXOMNI_MEDIA_NODE_ENDPOINT` as `http://<FLUXOMNI_MEDIA_NODE_PUBLIC_HOST>:50051`. Single-host compose installs use Docker-internal networking (`http://media-node:50051`) instead.

If this value points to a private hostname, a Docker-only hostname, or the wrong server, the control-plane can register the node with an address that other systems cannot reach.

Example:

```bash
FLUXOMNI_CONTROL_PLANE_IMAGE=ghcr.io/fluxomnia-systems/fluxomni-control-plane
FLUXOMNI_FRONTEND_IMAGE=ghcr.io/fluxomnia-systems/fluxomni-frontend
FLUXOMNI_MEDIA_NODE_IMAGE=ghcr.io/fluxomnia-systems/fluxomni-media-node
FLUXOMNI_VERSION=latest
FLUXOMNI_PUBLIC_HOST=control.example.com
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=control.example.com
```

`install.sh` also writes `FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN` automatically. Keep the same token on both services; rotate it only if you are restarting the whole stack together.
Published self-host releases serve the operator UI from the `frontend` container, so `FLUXOMNI_PUBLIC_HOST` and `FLUXOMNI_FRONTEND_HTTP_PORT` determine the browser URL you share with operators.
If you deploy behind a domain or reverse proxy, set `FLUXOMNI_PUBLIC_HOST`, `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST`, and `FLUXOMNI_PUBLIC_URL` (with the `https://` scheme) so generated URLs use the correct hostnames and scheme. See [Reverse Proxy & TLS](reverse-proxy.md) for examples.

## Release Channels

- `latest`: newest stable release and the default in this repository
- `vYY.Q.N`: canonical public stable release tag, e.g. `v26.2.4`
- `vX.Y.Z`: core image tag, accepted for direct image pinning, e.g. `v0.13.0`
- `edge`: latest successful publish from `main`

The installer maps canonical public pins to the matching core image tag when native date image tags are not published.

## Optional Variables

- `FLUXOMNI_FRONTEND_HTTP_PORT`: host HTTP port for the frontend UI and proxied API.
- `FLUXOMNI_CONTROL_PLANE_RPC_PORT`: host gRPC port for remote media-node registration and delivery. Defaults to localhost-only; expose it deliberately when attaching external media nodes.
- `FLUXOMNI_MEDIA_NODE_RTMP_PORT`: host RTMP ingest port.
- `FLUXOMNI_MEDIA_NODE_HLS_PORT`: host HLS TCP port.
- `FLUXOMNI_MEDIA_NODE_WHIP_PORT`: host WHIP signaling TCP port (default `8003`).
- `FLUXOMNI_SRS_RTC_PORT`: WebRTC media UDP listener and host port (default `8000`), independent of HLS.
- `FLUXOMNI_SRS_CANDIDATE`: reachable ICE candidate hostname/IP; defaults to the media-node public host when empty.
- `FLUXOMNI_MEDIA_NODE_SRS_CALLBACK_PORT`: host loopback port for the internal SRS callback listener.
- `FLUXOMNI_MEDIA_NODE_SRT_PORT`: host SRT UDP port.
- `FLUXOMNI_MEDIA_NODE_GRPC_PORT`: host gRPC port for a standalone media-node.
- `FLUXOMNI_CONTROL_PLANE_DATA_DIR`: control-plane app data directory on the host.
- `FLUXOMNI_MEDIA_NODE_DATA_DIR`: media-node app data directory on the host.
- `FLUXOMNI_SHARED_VIDEO_DIR`: host directory mounted read-only into the media-node video cache path.
- `FLUXOMNI_OTLP_ENDPOINT`: OpenTelemetry collector endpoint (e.g. `http://collector:4318`).

For single-host installs, keep both data-directory variables on `./data` unless you intentionally want separate storage surfaces.
If you move `FLUXOMNI_MEDIA_NODE_DATA_DIR` elsewhere, keep `FLUXOMNI_SHARED_VIDEO_DIR` pointed at the control-plane video cache so downloaded or imported playlist files remain readable from the media-node.

## Apply Changes

From your install directory:

```bash
docker compose up -d
```

The operator UI is served from the frontend host:

- `http://<FLUXOMNI_PUBLIC_HOST>` for the landing page
- `/routes` for route management
- `/fleet` for media-node monitoring

## Attach an External Media Node

The full self-host install binds the control-plane RPC listener to localhost by default.
Before attaching another media server, expose `50052/tcp` only to trusted node IPs, then run the installer on that server in explicit `media-node` mode.
`FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT`, `FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN`, and `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` are required for that mode:

```bash
FLUXOMNI_VERSION=edge \
FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT=http://control.example.com:50052 \
FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=replace-with-shared-token \
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=media2.example.com \
  curl -fsSL https://install.fluxomni.io | bash -s -- media-node
```

That mode installs into `~/fluxomni-media-node` by default, writes a media-node-only compose bundle, derives a host-specific node ID when one is not provided, and waits for a successful `Registered media node with control plane` log before printing success.
Set `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` to the hostname or IP that the control-plane, publishers, and viewers should use for that media server. In the example above, that is `media2.example.com`.

Set these only when you need to override the defaults:

- `FLUXOMNI_MEDIA_NODE_ENDPOINT`: advertised media-node gRPC endpoint. Defaults to `http://<FLUXOMNI_MEDIA_NODE_PUBLIC_HOST>:50051`.
- `FLUXOMNI_MEDIA_NODE_ID`: stable node ID. Defaults to `media-node-<hostname>`.
- `FLUXOMNI_MEDIA_NODE_NAME`: display name shown in the control-plane. Defaults to `Media Node <hostname>`.
- `FLUXOMNI_MEDIA_NODE_LABELS`: comma-separated labels for node capabilities or operator grouping. Defaults to `selfhost`.
- `FLUXOMNI_MEDIA_NODE_ZONE`: optional location or placement label. Defaults to `local`.

## Update to Newest Image for Current Tag

From your install directory:

```bash
docker compose pull
docker compose up -d
```

## Offline Preparation Resource Limits

Each media node can have its own shared budget for playlist normalization.
Live FFmpeg and SRS remain outside that preparation group. The Fleet node's
Diagnostics page shows the configured budget, current usage, throttling and
active/waiting preparation jobs.

This option requires a media-node build that supports preparation cgroups,
Linux with cgroup v2, a local rootful Docker daemon without user namespace
remapping, systemd, Python 3, and root/sudo access. The host must already enable
`cpu`, `memory` and `pids` in `/sys/fs/cgroup/cgroup.subtree_control`; the installer
does not change the host-wide controller policy. Docker Desktop, remote Docker
contexts and rootless Docker are not supported by this option.

Choose budgets for your machine; the following values are examples:

```bash
curl -fsSL https://install.fluxomni.io -o install.sh
FLUXOMNI_PREPARATION_CGROUP_ENABLED=1 \
FLUXOMNI_PREPARATION_CPU_MILLICORES=500 \
FLUXOMNI_PREPARATION_MEMORY_MIB=1024 \
FLUXOMNI_PREPARATION_TASKS=64 \
  bash install.sh full
```

Use `media-node` instead of `full` on a standalone node, alongside its usual
control-plane connection settings. Repeat on other node hosts with different
budgets. `500` millicores means half of one CPU core; memory is MiB and includes
charged page cache; tasks count threads, not just processes. Swap is disabled
for preparation. These limits do not predict how many additional live routes
or outputs will fit.

The installer saves the values in `.env`, downloads the common
`docker-compose.preparation-cgroup.yml` overlay and includes it in the installed
Compose bundle. Each installation directory gets a distinct hash-named group,
root-owned helper and boot unit. Keep installation directories stable. The unit
recreates the group before Docker starts after reboot, including socket
activation. No privileged media-node container or full writable cgroup mount
is added.

Installer reruns preserve budgets; an explicit environment value overrides its
saved value. To change just CPU, rerun with
`FLUXOMNI_PREPARATION_CPU_MILLICORES=750`. Alternatively, edit the enabled
installation's `.env` and run `docker compose up -d` to recreate the node.
The installer requires the current media-node startup to confirm enforcement,
so older images cannot pass using limits left by a previous version.
Check that Fleet reports **enforced** after recreation. CPU throttling slows
preparation; memory/task-limit events fail the preparation request. Shared
storage, memory bandwidth and GPU contention still need workload testing.

To disable, rerun the installer with
`FLUXOMNI_PREPARATION_CGROUP_ENABLED=0`. This removes the active overlay, disables
the boot unit and saves budgets as comments for a later explicit re-enable.
Changing the flag alone followed by `docker compose up` does not rebuild the
include: use the installer for enable/disable. Disabling never kills or deletes
the old cgroup. After a killed node, re-enabling lets the runtime recover its
owned attempts; live/runtime Docker limits cover a separate budget.

For manual deployments, provision a dedicated subtree, set
`FLUXOMNI_PREPARATION_HOST_ROOT` and all three budgets, then combine either base
Compose template with `docker-compose.preparation-cgroup.yml`. Do not share a
preparation root between nodes. Provide boot-time provisioning before Docker
restores the container. Installer-managed roots can be drained after stopping
the node with the root-owned helper's `cleanup <installation-hash>` command;
cleanup disables that installation's boot unit and refuses a live owner.
