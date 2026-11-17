# Fluxomni Self-Hosted

<p align="center">
  <img src="docs/src/images/logo.webp" alt="Fluxomni Logo" width="10%">
</p>

Fluxomni runs live streams and file-based channels on your own servers. Send one feed to several destinations using RTMP, SRT, or Icecast. Use the Fluxomni web app to manage routes, playlists, outputs, and media nodes.

This repository contains the files for self-hosted installs. Linux and macOS are supported on x64 and ARM64. Windows is supported through WSL2 with Ubuntu.

## What's New in 26.4.0

- **Recordings and rundowns** — preserve, rotate, and retain recordings in the Library; save reusable rundowns and apply them to an idle route
- **Playlist programming** — stingers, planned timing, weekday schedules, ahead-of-playback preparation, slideshows, and automatic thumbnails
- **Capacity ledger** — per-node route and output ceilings; the first upgrade from a running v26.3.x installation must stop old execution and initialize the ledger
- **Private media nodes** — outbound TLS control and Fleet enrollment, with no inbound control port required

Read the [26.4.0 upgrade guide](docs/src/getting-started/upgrade-26.4.0.md), [capacity ledger procedure](docs/src/getting-started/capacity-upgrades.md), and [release notes](docs/src/changelog.md). Custom API clients should pin `@fluxomni/api-client@26.4.0`.

## Quick Install

```bash
curl -fsSL https://install.fluxomni.io | bash
```

After installation:

- open `http://<your-server-ip>`
- use `/routes` to manage streams
- use `/fleet` to check server health
- copy the RTMP publish address from a route workspace

> [!NOTE]
> On Debian and Ubuntu, the installer can install Docker automatically if it is missing. That path requires `root` or `sudo` access.

## Choose Your Setup

### Self-Hosted Stack

Best for most users. Installs Fluxomni on one server.

```bash
curl -fsSL https://install.fluxomni.io | bash
```

### Standalone Media Node

Open Fleet → Add Node on the existing control plane as an Admin. Choose the node identity and generate a join command, then copy it to the remote server.

The installer exchanges a short-lived code over verified HTTPS and keeps the machine credential in owner-only `node-secrets/`. The node uses outbound TLS control; it needs no VPN, public address or inbound control port. Public media settings are optional.

See [Attach Another Media Node](docs/src/getting-started/quick-start.md#attach-another-media-node) for the current stable setup. Fleet enrollment uses matching `v26.4.0` images.

## Common Install Examples

```bash
# Install into a custom directory
curl -fsSL https://install.fluxomni.io | \
FLUXOMNI_DIR=/opt/fluxomni \
  bash

# Pin a specific stable release
curl -fsSL https://install.fluxomni.io | \
FLUXOMNI_VERSION=v26.4.0 \
  bash

# Use the newest main-branch build
curl -fsSL https://install.fluxomni.io | \
FLUXOMNI_VERSION=edge \
  bash

# Use a custom self-host config ref
curl -fsSL https://install.fluxomni.io | \
FLUXOMNI_SELFHOST_REF=my-ref \
  bash
```

## What the Installer Does

For the default self-host setup, the installer:

- installs Docker automatically on supported Debian and Ubuntu hosts if needed
- downloads the correct `docker-compose.yml` and `.env.example`
- creates or updates `.env` in place
- pulls and starts Fluxomni
- preserves your existing `data/` directory on reruns
- checks that the local services start before reporting success

The web UI is included in the default install.

## Installed Files and Default Paths

| Install type | Default directory | Main services |
| --- | --- | --- |
| Self-hosted stack | `~/fluxomni` | Fluxomni |
| Standalone media node | `~/fluxomni-media-node` | `media-node` |

The installer manages:

- `docker-compose.yml`
- `.env`
- `data/` for state, recordings, downloaded videos, and runtime files

## Release Channels

| Channel | Description |
| --- | --- |
| `latest` | Newest stable release (default) |
| `vYY.Q.N` | Canonical public stable release tag |
| `vX.Y.Z` | Core image tag, accepted for direct image pinning |
| `edge` | Latest successful publish from `main` |

The public launcher selects installer code and assets from the same release. `latest` uses the published stable installer; `edge` uses the new runtime installer. Version pins and saved versions keep their release-specific workflow.

Use `latest` unless you need a pinned release or a test build. The current stable public release is `v26.4.0`. Retained image tags are available for separately reviewed recovery; migrated state must not be restarted with predecessor images.

See the What's New section above for recent changes.

## Manage Your Instance

If you used the default single-host install:

```bash
cd ~/fluxomni

# Troubleshooting (Connection & Health Doctor)
fluxomnictl doctor

# Supporting newer releases require the capacity-ledger maintenance procedure below

# Follow logs
docker compose logs -f

# Planned stop: first disable and drain routes using the capacity upgrade guide
docker compose --profile auto-update stop --timeout 30
```

If you used a custom directory or installed only a media node, pass `--dir` to `fluxomnictl`, or run `./doctor.sh` from that directory.

If `fluxomnictl` is missing, download the current launcher and run `bash install.sh tools`. A `curl | bash` install does not leave `install.sh` on disk. `tools` does not pull images or restart services. It looks in `~/fluxomni` and `~/fluxomni-media-node` unless you set `FLUXOMNI_DIR`. Root gets `/usr/local/bin/fluxomnictl`. Other users get `~/.local/bin/fluxomnictl`.

Installer reruns preserve data and known `.env` settings. v26.3.2 keeps its release-specific rerun behavior. v26.4.0 requires an explicit capacity maintenance mode on established installations. Follow the [capacity upgrade guide](docs/src/getting-started/capacity-upgrades.md) for initial upgrades, later drained upgrades and standalone nodes.

For SRS open-file errors, rerun the latest installer; see [troubleshooting](docs/src/getting-started/troubleshooting.md#srs-reports-too-few-open-files).

## Advanced Installer Notes

- If `FLUXOMNI_VERSION` is pinned, the installer tries the matching self-host files first. The installer reports an error if files for a pinned stable public release are missing after release sync.
- Use `FLUXOMNI_SELFHOST_REF` to force a self-host asset ref.
- Use `FLUXOMNI_REPO_RAW` to use a custom raw asset base.
- The installer requires Compose 2.20+ and writes `docker-compose.yml`, `compose.defaults.yml`, and `compose.release.yml`. Keep them together. Put custom settings in `docker-compose.override.yml`.
- Use `FLUXOMNI_FRONTEND_IMAGE`, `FLUXOMNI_CONTROL_PLANE_IMAGE`, and `FLUXOMNI_MEDIA_NODE_IMAGE` only when you publish your own images.

Useful standalone media-node overrides:

- `FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` — optional public media URLs
- `FLUXOMNI_MEDIA_NODE_HTTP_HOST` — optional HTTP media relay
- `FLUXOMNI_MEDIA_NODE_ID`
- `FLUXOMNI_MEDIA_NODE_NAME`
- `FLUXOMNI_MEDIA_NODE_LABELS`
- `FLUXOMNI_MEDIA_NODE_CAPABILITIES` — optional declared capabilities
- `FLUXOMNI_MEDIA_NODE_PRIVATE_NETWORK_ONLY` — optional private-network flag
- `FLUXOMNI_MEDIA_NODE_ZONE`

## Documentation

Use these guides for setup and operation:

- [Published documentation](https://docs.fluxomni.io/)
- [Book introduction](./docs/src/README.md)
- [Roadmap](./docs/src/roadmap.md)
- [Quick start](./docs/src/getting-started/quick-start.md)
- [Configuration](./docs/src/getting-started/configuration.md)
- [Private Access & Tunnels](./docs/src/getting-started/private-access.md)
- [Troubleshooting](./docs/src/getting-started/troubleshooting.md)
- [Deployment overview](./docs/src/deployment/overview.md)
- [Hetzner guide](./docs/src/deployment/hetzner.md)
- [DigitalOcean guide](./docs/src/deployment/digitalocean.md)
- [Oracle guide](./docs/src/deployment/oracle.md)
- [Vscale guide](./docs/src/deployment/vscale.md)

The published site opens the latest stable release. Use **Docs version** to
open the same guide for a tagged release or switch to **Edge** for the guides
on `main`. If the selected version has no matching page, the switcher opens
that version's introduction.

## Working on This Repository

This repository builds the published docs website from the `docs/` mdBook.
Changes on `main` appear under `/edge/`. The site root comes from the
`latestStable` entry in `docs/src/release-manifest.json` and its matching
self-host tag. Each listed release with a tagged book also gets a permanent
path, such as `/v26.4.0/`. Releases without a tagged book are omitted from
the switcher.

To publish stable docs, merge the release sync, tag the self-host commit
that contains the matching docs and install assets, and publish the GitHub
release. Until the matching tag exists, Pages keeps serving the previous
tagged release at the root. Pages keeps the first artifact deployed for a
commit, so a retag of that same commit does not refresh the live site.
Publish again from a new commit on main after the stable tag points at the
docs to serve.

To preview all versions locally, fetch the release tags and build into an
empty directory with Python 3.12 or newer:

```bash
git fetch --tags
docs_preview="$(mktemp -d)"
python3 scripts/build-versioned-docs.py --output "$docs_preview"
python3 -m http.server 8000 --directory "$docs_preview"
```

Before opening a PR that changes docs or the installer, run:

```bash
make lint
```

For the same strict check used in CI:

```bash
make lint.ci
```

Useful local commands:

- `make build` - build the docs into `docs/book`
- `make serve` - serve the docs locally
- `make lint` - build docs, check local Markdown links, and run markdownlint when available
- `make lint.ci` - strict CI docs lint; requires `markdownlint-cli2`
- `make screenshots` - refresh user-guide page and guided-flow screenshots from a running Fluxomni instance

Compatibility aliases still exist for the older `make docs.build`, `make docs.serve`, `make docs.lint`, and `make docs.lint.ci` targets.

### User-Guide Screenshots

```bash
# Against a local Docker stack (default http://localhost)
make screenshots

# Against a specific host
FLUXOMNI_URL=http://192.168.1.100 make screenshots

# With auth enabled
FLUXOMNI_URL=http://192.168.1.100 FLUXOMNI_ADMIN_PASSWORD=secret make screenshots
```

See `screenshots/README.md` for the full image list and capture details. v26.4.0 operator stills and videos are regenerated with `npm run capture:v264` from `screenshots/` against a running v26.4.0 instance. Stills are written to `docs/src/images/user-guide/v264/`. Leave `FLUXOMNI_VIDEO_OUTPUT_DIR` unset so the WebMs are written to `docs/src/videos/user-guide/`.

Playlist normalization can use explicit per-node preparation CPU/memory/thread budgets.
See [preparation resource limits](docs/src/getting-started/configuration.md#offline-preparation-resource-limits)
for installer enablement, reboot provisioning and manual Compose deployment.

Media-node credential rotation, recovery and revocation are available from Fleet. Follow the [credential replacement procedure](docs/src/getting-started/quick-start.md#rotate-or-recover-a-node-credential) to preserve node identity and verified execution ownership.
