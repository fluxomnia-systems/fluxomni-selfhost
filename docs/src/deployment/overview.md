# Deployment

FluxOmni can be deployed on any Linux server that runs Docker.
The installer handles everything — Docker installation, firewall setup, and starting the stack — from a single command.

## Quick Install

```bash
curl -fsSL https://install.fluxomni.io | bash -s
```

On Debian/Ubuntu hosts, this automatically installs Docker if it is missing.
The default install path is `~/fluxomni`.

## General Requirements

- **OS**: Ubuntu 24.04 LTS (recommended and tested; other Debian-based systems may work)
- **Docker**: Engine with Compose v2 — the installer bootstraps Docker automatically on Debian/Ubuntu
- **Ports**: see the [Configuration](../getting-started/configuration.md) page for the full port list

For the smallest restreaming workloads, a 1-vCPU / 1 GB instance is usually enough.
If you plan to run many concurrent streams or use transcoding, size up accordingly.

## Cloud Provider Guides

Step-by-step instructions for creating a server and auto-installing FluxOmni:

- [DigitalOcean](digitalocean.md) — Droplets
- [Hetzner Cloud](hetzner.md) — Cloud Servers
- [Oracle Cloud](oracle.md) — OCI Compute (includes Free Tier notes)
- [VScale / Selectel](vscale.md) — Moscow / St. Petersburg regions

Each guide ends with FluxOmni running at `http://<server-ip>/routes`.

## Installer Variables

The installer accepts environment variables to control its behavior.
Pass them before the pipe, for example:

```bash
curl -fsSL https://install.fluxomni.io | WITH_UFW=1 FLUXOMNI_VERSION=edge bash -s
```

### Server provisioning

- `WITH_INITIAL_UPGRADE=1` — run `apt-get upgrade` before installing (useful for fresh servers)
- `WITH_UFW=1` — install and configure ufw with the required FluxOmni ports
- `WITH_FIREWALLD=1` — install and configure firewalld instead of ufw (required for Oracle Cloud)
- `ALLOWED_IPS` — comma-separated list of IPs to allow through the firewall (default: `*` for all)

### Install target

- `FLUXOMNI_DIR` — install path (default: `~/fluxomni`, or `~/fluxomni-media-node` for media-node installs)
- `FLUXOMNI_VERSION` — image tag: `latest` (default), `edge`, or `vX.Y.Z`
- `FLUXOMNI_CONTROL_PLANE_IMAGE` — override control-plane image repository
- `FLUXOMNI_MEDIA_NODE_IMAGE` — override media-node image repository
- `FLUXOMNI_IMAGE` — legacy base repository override (derives split image names when explicit variables are unset)
- `FLUXOMNI_SELFHOST_REF` — force a specific self-host config bundle ref
- `FLUXOMNI_REPO_RAW` — override the raw asset base entirely

### Media-node mode

Install a standalone media-node by passing `media-node` as a positional argument:

```bash
FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT=http://control.example.com:50052 \
FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=replace-with-shared-token \
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=media2.example.com \
  curl -fsSL https://install.fluxomni.io | bash -s -- media-node
```

Required variables: `FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT`, `FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN`, and `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST`.

Optional media-node overrides: `FLUXOMNI_MEDIA_NODE_ENDPOINT`, `FLUXOMNI_MEDIA_NODE_ID`, `FLUXOMNI_MEDIA_NODE_NAME`, `FLUXOMNI_MEDIA_NODE_LABELS`, `FLUXOMNI_MEDIA_NODE_ZONE`.

## Release Channels

- `latest`: newest stable release
- `vX.Y.Z`: immutable stable release image
- `edge`: latest successful publish from `main`

When `FLUXOMNI_VERSION` is pinned, the installer first tries the same self-host ref and falls back to `main` if versioned self-host assets are not published yet.

## After Deployment

Once the stack is running:

- [Configuration](../getting-started/configuration.md) — environment variables, release channels, attaching media nodes
- [Troubleshooting](../getting-started/troubleshooting.md) — logs, common issues, rollback
- [User Guide](../user-guide/overview.md) — operating the control surface
