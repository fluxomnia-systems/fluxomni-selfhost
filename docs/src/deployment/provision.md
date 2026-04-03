# Server Provisioning

This directory contains provisioning assets for unattended server setup.

## Files

- [`provision.sh`](https://github.com/fluxomnia-systems/fluxomni-selfhost/blob/main/provision.sh): installs Docker (if needed), configures optional firewall rules, and installs FluxOmni.

Development-only assets (for internal build workflows) are kept outside this user-facing docs tree.

## Quick Usage

Provision the full single-host stack:

```bash
curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/provision.sh | bash
```

That path provisions one host running both `control-plane` and `media-node`.
The published `control-plane` image currently embeds the operator UI, so the default self-host path does not require a separate frontend image.

Provision only a standalone media-node:

```bash
curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/provision.sh | \
  FLUXOMNI_VERSION=edge \
  FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT=http://control.example.com:50052 \
  FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=replace-with-shared-token \
  FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=media2.example.com \
  bash -s -- media-node
```

Optional variables:

- `FLUXOMNI_INSTALL_TARGET` (default: `full`; same values as the positional `full|media-node` argument)
- `FLUXOMNI_VERSION` (default: `latest`)
- `FLUXOMNI_CONTROL_PLANE_IMAGE` (default: derived from `ghcr.io/fluxomnia-systems/fluxomni`)
- `FLUXOMNI_MEDIA_NODE_IMAGE` (default: derived from `ghcr.io/fluxomnia-systems/fluxomni`)
- `FLUXOMNI_IMAGE` (legacy base repository override used only when the explicit split-image variables are unset)
- `FLUXOMNI_DIR` (default: `/opt/fluxomni` for full installs, `/opt/fluxomni-media-node` for `media-node` installs)
- `FLUXOMNI_SELFHOST_REF` (force a specific self-host config ref)
- `FLUXOMNI_REPO_RAW` (override the raw asset base entirely)
- `WITH_INITIAL_UPGRADE=1`
- `WITH_FIREWALLD=1`
- `ALLOWED_IPS` (default: `*`)

When `FLUXOMNI_VERSION` is pinned, provisioning first tries the same self-host ref and falls back to `main` if versioned self-host assets are not published yet. Use `FLUXOMNI_SELFHOST_REF` only if the config bundle needs to come from a different ref.

`media-node` provisioning notes:

- Required installer inputs: `FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT`, `FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN`, and `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST`
- Firewall defaults for full installs open the control-plane RPC port (`50052`)
- Firewall defaults for `media-node` installs open the advertised media-node gRPC port (`50051`)

Release channels:

- `latest`: newest stable release
- `vX.Y.Z`: immutable stable release image
- `edge`: latest successful publish from `main`

After provisioning finishes, open `http://<server-ip>/routes` for route management and `http://<server-ip>/fleet` for attached media-node monitoring.
