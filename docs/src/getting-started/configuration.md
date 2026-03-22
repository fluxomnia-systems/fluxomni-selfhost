# Configuration

FluxOmni is configured through environment variables in `.env`.

## Core Variables

- `FLUXOMNI_CONTROL_PLANE_IMAGE`: control-plane image repository.
- `FLUXOMNI_MEDIA_NODE_IMAGE`: media-node image repository.
- `FLUXOMNI_VERSION`: Image tag to deploy.
- `FLUXOMNI_PUBLIC_HOST`: Public hostname/IP shown for the control surface.
- `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST`: Public hostname/IP shown in RTMP, HLS, SRT, and WebRTC media URLs.

Example:

```bash
FLUXOMNI_CONTROL_PLANE_IMAGE=ghcr.io/fluxomnia-systems/fluxomni-control-plane
FLUXOMNI_MEDIA_NODE_IMAGE=ghcr.io/fluxomnia-systems/fluxomni-media-node
FLUXOMNI_VERSION=latest
FLUXOMNI_PUBLIC_HOST=203.0.113.10
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=203.0.113.10
```

`install.sh` also writes `FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN` automatically. Keep the same token on both services; rotate it only if you are restarting the whole stack together.

## Release Channels

- `latest`: newest stable release and the default in this repository
- `vX.Y.Z`: immutable image tag for a specific stable release
- `edge`: latest successful publish from `main`

## Optional Variables

- `FLUXOMNI_CONTROL_PLANE_HTTP_PORT`: host HTTP port for the embedded UI and API.
- `FLUXOMNI_MEDIA_NODE_RTMP_PORT`: host RTMP ingest port.
- `FLUXOMNI_MEDIA_NODE_HLS_PORT`: host HLS/WebRTC port.
- `FLUXOMNI_MEDIA_NODE_SRT_PORT`: host SRT UDP port.
- `FLUXOMNI_CONTROL_PLANE_DATA_DIR`: control-plane app data directory on the host.
- `FLUXOMNI_MEDIA_NODE_DATA_DIR`: media-node app data directory on the host.
- `FLUXOMNI_SHARED_VIDEO_DIR`: host directory mounted read-only into the media-node video cache path.
- `FLUXOMNI_OTLP_COLLECTOR_IP`: OpenTelemetry collector host.
- `FLUXOMNI_OTLP_COLLECTOR_PORT`: OpenTelemetry collector port.

For single-host installs, keep both data-directory variables on `./data` unless you intentionally want separate storage surfaces.
If you move `FLUXOMNI_MEDIA_NODE_DATA_DIR` elsewhere, keep `FLUXOMNI_SHARED_VIDEO_DIR` pointed at the control-plane video cache so downloaded or imported playlist files remain readable from the media-node.

## Apply Changes

```bash
cd ~/fluxomni
docker compose up -d
```

## Update to Newest Image for Current Tag

```bash
cd ~/fluxomni
docker compose pull
docker compose up -d
```
