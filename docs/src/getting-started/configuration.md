# Configuration

FluxOmni is configured through environment variables in `.env`.

## Core Variables

- `FLUXOMNI_CONTROL_PLANE_IMAGE`: control-plane image repository.
- `FLUXOMNI_MEDIA_NODE_IMAGE`: media-node image repository.
- `FLUXOMNI_VERSION`: Image tag to deploy.
- `FLUXOMNI_PUBLIC_HOST`: Public hostname/IP shown for the control surface.
- `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST`: Public hostname/IP shown in RTMP, HLS, SRT, and WebRTC media URLs.
- `FLUXOMNI_CONTROL_PLANE_RPC_PORT`: Host port that publishes the control-plane gRPC listener.
- `FLUXOMNI_MEDIA_NODE_GRPC_PORT`: Host port that publishes the standalone media-node gRPC listener.

`FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` is especially important for standalone media-node installs.
FluxOmni uses it in two places:

- It is shown in the RTMP, HLS, SRT, and WebRTC URLs that operators and publishers use.
- It is used to derive the default `FLUXOMNI_MEDIA_NODE_ENDPOINT` as `http://<FLUXOMNI_MEDIA_NODE_PUBLIC_HOST>:50051`.

If this value points to a private hostname, a Docker-only hostname, or the wrong server, the control-plane can register the node with an address that other systems cannot reach.

Example:

```bash
FLUXOMNI_CONTROL_PLANE_IMAGE=ghcr.io/fluxomnia-systems/fluxomni-control-plane
FLUXOMNI_MEDIA_NODE_IMAGE=ghcr.io/fluxomnia-systems/fluxomni-media-node
FLUXOMNI_VERSION=latest
FLUXOMNI_PUBLIC_HOST=control.example.com
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=control.example.com
```

`install.sh` also writes `FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN` automatically. Keep the same token on both services; rotate it only if you are restarting the whole stack together.

## Release Channels

- `latest`: newest stable release and the default in this repository
- `vX.Y.Z`: immutable image tag for a specific stable release
- `edge`: latest successful publish from `main`

## Optional Variables

- `FLUXOMNI_CONTROL_PLANE_HTTP_PORT`: host HTTP port for the embedded UI and API.
- `FLUXOMNI_CONTROL_PLANE_RPC_PORT`: host gRPC port for remote media-node registration and delivery.
- `FLUXOMNI_MEDIA_NODE_RTMP_PORT`: host RTMP ingest port.
- `FLUXOMNI_MEDIA_NODE_HLS_PORT`: host HLS/WebRTC port.
- `FLUXOMNI_MEDIA_NODE_SRT_PORT`: host SRT UDP port.
- `FLUXOMNI_MEDIA_NODE_GRPC_PORT`: host gRPC port for a standalone media-node.
- `FLUXOMNI_CONTROL_PLANE_DATA_DIR`: control-plane app data directory on the host.
- `FLUXOMNI_MEDIA_NODE_DATA_DIR`: media-node app data directory on the host.
- `FLUXOMNI_SHARED_VIDEO_DIR`: host directory mounted read-only into the media-node video cache path.
- `FLUXOMNI_OTLP_ENDPOINT`: OpenTelemetry collector endpoint (e.g. `http://collector:4318`).

For single-host installs, keep both data-directory variables on `./data` unless you intentionally want separate storage surfaces.
If you move `FLUXOMNI_MEDIA_NODE_DATA_DIR` elsewhere, keep `FLUXOMNI_SHARED_VIDEO_DIR` pointed at the control-plane video cache so downloaded or imported playlist files remain readable from the media-node.

## Apply Changes

```bash
cd ~/fluxomni
docker compose up -d
```

## Attach an External Media Node

The full self-host install now publishes the control-plane RPC listener on TCP `50052` by default.
To attach another media server, run the installer on that server in explicit `media-node` mode:

```bash
FLUXOMNI_VERSION=edge \
FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT=http://control.example.com:50052 \
FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=replace-with-shared-token \
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=media2.example.com \
  curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash -s -- media-node
```

That mode installs into `~/fluxomni-media-node` by default, writes a media-node-only compose bundle, derives a host-specific node ID when one is not provided, and waits for a successful `Registered media node with control plane` log before printing success.
Set `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` to the hostname or IP that the control-plane, publishers, and viewers should use for that media server. In the example above, that is `media2.example.com`.

Set these only when you need to override the defaults:

- `FLUXOMNI_MEDIA_NODE_ENDPOINT`: advertised media-node gRPC endpoint. Defaults to `http://<FLUXOMNI_MEDIA_NODE_PUBLIC_HOST>:50051`.
- `FLUXOMNI_MEDIA_NODE_ID`: stable node ID. Defaults to `media-node-<hostname>`.
- `FLUXOMNI_MEDIA_NODE_NAME`: display name shown in the control-plane. Defaults to `Media Node <hostname>`.

## Update to Newest Image for Current Tag

```bash
cd ~/fluxomni
docker compose pull
docker compose up -d
```
