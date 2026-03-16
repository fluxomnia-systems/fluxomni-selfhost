# Quick Start

Get FluxOmni running in minutes.

## Prerequisites

- `curl`
- `root` or `sudo` access on Debian/Ubuntu if Docker is not already installed

If Docker is already available, the installer uses it directly. Manual installs and non-Debian hosts still require Docker Engine with Docker Compose v2.

## One-line Install

```bash
curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash
```

By default, FluxOmni installs to `~/fluxomni` and follows the newest stable release channel (`latest`).

## Install with Custom Values

This example opts into the `edge` channel and a custom install path:

```bash
FLUXOMNI_DIR=/opt/fluxomni \
FLUXOMNI_VERSION=edge \
FLUXOMNI_IMAGE=ghcr.io/fluxomnia-systems/fluxomni \
  curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash
```

To pin a specific stable release instead, set `FLUXOMNI_VERSION=vX.Y.Z`.

For pinned installs, the installer uses the same self-host ref by default. Use `FLUXOMNI_SELFHOST_REF` only if the config bundle needs to come from a different ref.

## Manual Install

```bash
ASSET_REF=main # or the same pinned version, for example vX.Y.Z
mkdir -p ~/fluxomni
cd ~/fluxomni
curl -fsSL "https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/${ASSET_REF}/docker-compose.yml" -o docker-compose.yml
curl -fsSL "https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/${ASSET_REF}/.env.example" -o .env
mkdir -p data/videos data/dvr
touch data/state.json data/srs.conf
docker compose up -d
```

## Next Steps

- Configure [authentication and settings](configuration.md)
- Review [cloud deployment guides](../deployment/)
- Use [troubleshooting](troubleshooting.md) if startup fails
