# FluxOmni

<p align="center">
  <img src="images/logo.webp" alt="FluxOmni Logo" width="10%">
</p>

FluxOmni is a multi-protocol live streaming platform for broadcasting one source to multiple destinations (RTMP, SRT, Icecast) simultaneously.
Current self-host releases run a split `control-plane` + `media-node` topology, even on a single host.

This repository contains self-host installation and deployment documentation only.

## Install in one command

Install FluxOmni:

```bash
curl -fsSL https://install.fluxomni.io | bash
```

The installer defaults to the newest stable image (`latest`). Use `FLUXOMNI_VERSION=edge` only if you want the latest main-branch build.
For pinned versions, the installer first tries the same self-host ref and falls back to `main` if versioned self-host assets are not published yet.
The default install remains single-host, but it now runs split `control-plane` and `media-node` containers with a shared `./data` root.
The published `control-plane` image currently embeds the operator UI, so no separate frontend image is required on the default release path.
To attach a remote media server instead of the full stack, run the same installer as `bash -s -- media-node` on that host.

After installation:

- Control surface: `http://<your-server-ip>`
- Routes: `http://<your-server-ip>/routes`
- Fleet: `http://<your-server-ip>/fleet`
- RTMP ingest: copy the generated publish address from the [route workspace](user-guide/routes.md#route-workspace) (e.g. `rtmp://<your-server-ip>:1935/live/<publish-key>`)

## Documentation Sections

- [Changelog](changelog.md) — what's new in each release
- [Quick Start](getting-started/quick-start.md)
- [Configuration](getting-started/configuration.md)
- [Troubleshooting](getting-started/troubleshooting.md)
- [User Guide](user-guide/overview.md) — operating the Control Surface
- [Deployment](deployment/overview.md) — cloud provider guides and server provisioning

## Release Channels

- `latest`: newest stable release
- `vX.Y.Z`: immutable release image for a specific release
- `edge`: latest successful publish from `main`

## Support

- Found an issue? Open it in the [self-host repository issue tracker](https://github.com/fluxomnia-systems/fluxomni-selfhost/issues)
