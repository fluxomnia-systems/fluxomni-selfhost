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

- `FLUXOMNI_VERSION` or `FLUXOMNI_VER` (default: `edge`)
- `FLUXOMNI_IMAGE` (default: `ghcr.io/fluxomnia-systems/fluxomni`)
- `FLUXOMNI_DIR` (default: `/opt/fluxomni`)
- `WITH_INITIAL_UPGRADE=1`
- `WITH_FIREWALLD=1`
- `ALLOWED_IPS` (default: `*`)
