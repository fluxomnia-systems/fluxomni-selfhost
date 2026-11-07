# Deployment

Fluxomni deploys to Docker hosts on Linux, macOS, or Windows (WSL2 Ubuntu).
The installer downloads the stack, starts it, and can install Docker on Debian/Ubuntu. Firewall configuration is opt-in: enable it with `WITH_UFW=1` or `WITH_FIREWALLD=1` when running the installer.

## Quick Install

```bash
curl -fsSL https://install.fluxomni.io | bash -s
```

From the installer release after v26.4.0, a new Linux host with a normal Docker Engine also turns preparation limits on. Docker Desktop and WSL stay off. The installer prints the budgets. Set `FLUXOMNI_PREPARATION_CGROUP_ENABLED=0` before `bash` to skip them.

On Debian/Ubuntu hosts, this automatically installs Docker if it is missing.
The default install path is `~/fluxomni`.

## General Requirements

- **Supported platforms**: Linux x64/ARM64, macOS x64/Apple Silicon, Windows (WSL2 Ubuntu)
- **Recommended server OS**: Ubuntu 24.04 LTS
- **Architecture**: x86_64 (x64) or ARM64 (AArch64)
- **Docker**: Engine with Compose v2 — the installer installs Docker automatically on Debian/Ubuntu
- **Ports**: see the [Configuration](../getting-started/configuration.md) page for the full port list

Choose a server for the full stack, not just its media container. Use the
[measured sizing guide](../getting-started/sizing.md) to plan tests for your
input count, outputs, bitrate, and processing mode.

## Cloud Provider Guides

Follow these guides to create a server and install Fluxomni automatically:

- [DigitalOcean](digitalocean.md) — Droplets
- [Hetzner Cloud](hetzner.md) — Cloud Servers
- [Oracle Cloud](oracle.md) — OCI Compute (includes Free Tier notes)
- [VScale / Selectel](vscale.md) — Moscow / St. Petersburg regions

Each guide ends with Fluxomni running at `http://<server-ip>/routes`.

## Installer Variables

The installer accepts environment variables to control its behavior.
Pass them to `bash` after the pipe, for example:

```bash
curl -fsSL https://install.fluxomni.io | WITH_UFW=1 FLUXOMNI_VERSION=edge bash -s
```

### Server provisioning

- `WITH_INITIAL_UPGRADE=1` — run `apt-get upgrade` before installing (useful for fresh servers)
- `WITH_UFW=1` — install and configure ufw with the required Fluxomni ports
- `WITH_FIREWALLD=1` — install and configure firewalld instead of ufw (required for Oracle Cloud)
- `ALLOWED_IPS` — comma-separated list of IPs to allow through the firewall (default: `*` for all)

### Install target

- `FLUXOMNI_DIR` — install path (default: `~/fluxomni`, or `~/fluxomni-media-node` for media-node installs)
- `FLUXOMNI_VERSION` — image tag: `latest` (default), `edge`, canonical public `vYY.Q.N`, or core-image `vX.Y.Z`
- `FLUXOMNI_FRONTEND_IMAGE` — override frontend image repository
- `FLUXOMNI_CONTROL_PLANE_IMAGE` — override control-plane image repository
- `FLUXOMNI_MEDIA_NODE_IMAGE` — override media-node image repository
- `FLUXOMNI_IMAGE` — legacy base repository override (derives split image names when explicit variables are unset)
- `FLUXOMNI_SELFHOST_REF` — force a specific self-host config bundle ref
- `FLUXOMNI_REPO_RAW` — override the raw asset base entirely

### Media-node mode

Open Fleet → Add Node as an Admin. **Enrollment URL** has to be the control plane HTTPS address the new node can reach, or **Generate join command** stays disabled. Copy the command and run it on the remote host.

The command sets `FLUXOMNI_ENROLLMENT_URL`, `FLUXOMNI_ENROLLMENT_CODE`, `FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT`, and the node ID. Those values are short-lived installer inputs. The machine credential stays in `node-secrets/`. Follow [Attach Another Media Node](../getting-started/quick-start.md#attach-another-media-node).

## Release Channels

- `latest`: newest stable release
- `vYY.Q.N`: canonical public stable release tag, e.g. `v26.2.4`
- `vX.Y.Z`: core image tag, accepted for direct image pinning, e.g. `v0.13.0`
- `edge`: latest successful publish from `main`

For a pinned release, the installer tries the matching self-host ref and then its public/core alias when one exists. If assets for a stable public pin are missing, installation fails. Core-image pins can fall back to `main` with a warning. Use `FLUXOMNI_SELFHOST_REF` or `FLUXOMNI_REPO_RAW` only when you intend to choose another config source.

## After Deployment

Once the stack is running:

- [Configuration](../getting-started/configuration.md) — environment variables, release channels, attaching media nodes
- [Troubleshooting](../getting-started/troubleshooting.md) — logs, common issues, rollback
- [User Guide](../user-guide/overview.md) — operating the control surface
