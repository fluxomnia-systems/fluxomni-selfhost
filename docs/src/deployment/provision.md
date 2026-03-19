# Server Provisioning

This directory contains provisioning assets for unattended server setup.

## Files

- [`provision.sh`](https://github.com/fluxomnia-systems/fluxomni-selfhost/blob/main/provision.sh): installs Docker (if needed), configures optional firewall rules, and installs FluxOmni.

Development-only assets (for internal build workflows) are kept outside this user-facing docs tree.

## Quick Usage

```bash
curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/provision.sh | bash
```

Optional variables:

- `FLUXOMNI_VERSION` (default: `latest`)
- `FLUXOMNI_IMAGE` (default: `ghcr.io/fluxomnia-systems/fluxomni`)
- `FLUXOMNI_DIR` (default: `/opt/fluxomni`)
- `FLUXOMNI_SELFHOST_REF` (force a specific self-host config ref)
- `FLUXOMNI_REPO_RAW` (override the raw asset base entirely)
- `WITH_INITIAL_UPGRADE=1`
- `WITH_FIREWALLD=1`
- `ALLOWED_IPS` (default: `*`)

When `FLUXOMNI_VERSION` is pinned, provisioning first tries the same self-host ref and falls back to `main` if versioned self-host assets are not published yet. Use `FLUXOMNI_SELFHOST_REF` only if the config bundle needs to come from a different ref.

Release channels:

- `latest`: newest stable release
- `vX.Y.Z`: immutable stable release image
- `edge`: latest successful publish from `main`
