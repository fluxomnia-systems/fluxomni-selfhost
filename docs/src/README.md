# Fluxomni Studio

<p align="center">
  <img src="images/logo.webp" alt="Fluxomni Studio Logo" width="10%">
</p>

Fluxomni Studio runs live streams and file-based channels on your own servers. Send one feed to several destinations using RTMP, SRT, or Icecast. Use the browser UI to manage routes, playlists, outputs, and media nodes.

This repository contains self-host installation and deployment documentation only.

## Install in one command

Install Fluxomni Studio:

```bash
curl -fsSL https://install.fluxomni.io | bash
```

By default, the installer uses the newest stable release and installs Fluxomni Studio on one server.

Use `FLUXOMNI_VERSION=edge` only when you want the newest main-branch build. Use a canonical public tag like `v26.3.2` when you need a pinned stable release. Retained image tags require a separately reviewed recovery procedure when state has migrated.

To add a remote media server, run the same installer on that server with `bash -s -- media-node`.

After installation, open `http://<your-server-ip>/routes` and follow [First Stream](getting-started/first-stream.md). It shows how to create the first admin account, accept an RTMP source, add an output, check playback, and create your first backup.

Choose a guide for your task:

- **Run one stream on one server** — [Quick Start](getting-started/quick-start.md), then [First Stream](getting-started/first-stream.md)
- **Deploy on a cloud provider** — [Deployment](deployment/overview.md)
- **Secure a browser-accessible deployment** — [Reverse Proxy & TLS](getting-started/reverse-proxy.md) or [Private Access & Tunnels](getting-started/private-access.md)
- **Operate routes and media nodes** — [User Guide](user-guide/overview.md)
- **Automate an installation** — [API Automation](api/overview.md)

## New in 26.3.2

Read the [release notes](changelog.md) and [upgrade guide](getting-started/upgrade-26.3.2.md) before updating custom API clients. The [sizing guide](getting-started/sizing.md) uses measurements to explain the different costs of empty routes, live inputs, and multiple outputs.

## Documentation Sections

- [Quick Start](getting-started/quick-start.md) — install Fluxomni Studio
- [First Stream](getting-started/first-stream.md) — create your first route, publish a stream, check playback, and back up your setup
- [Deployment](deployment/overview.md) — cloud provider guides and server setup
- [User Guide](user-guide/overview.md) — operate the Control Surface, including Attention, Routes, Fleet, and settings
- [Configuration](getting-started/configuration.md) — configure access, networking, and runtime variables
- [Monitoring](getting-started/monitoring.md), [Backup & Restore](getting-started/backup.md), and [Troubleshooting](getting-started/troubleshooting.md) — maintain an installation
- [Scenarios](scenarios/README.md) — choose a guided deployment pattern
- [API Automation](api/overview.md) — session authentication, raw GraphQL, the TypeScript client, subscriptions, errors, and workflow examples
- [Changelog](changelog.md) and [Roadmap](roadmap.md) — product updates and direction

## Release Channels

- `latest`: newest stable release
- `vYY.Q.N`: canonical public stable release tag
- `vX.Y.Z`: core image tag, accepted for direct image pinning
- `edge`: latest successful publish from `main`

## Support

- Report issues in the [self-host repository issue tracker](https://github.com/fluxomnia-systems/fluxomni-selfhost/issues)
