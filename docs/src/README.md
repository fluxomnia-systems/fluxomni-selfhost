# Fluxomni Studio

<p align="center">
  <img src="images/logo.webp" alt="Fluxomni Studio Logo" width="10%">
</p>

Fluxomni Studio runs live streams on your own server. Send one stream in. Fluxomni Studio can send it out to many places at once: RTMP, SRT, or Icecast.

This repository contains self-host installation and deployment documentation only.

## Install in one command

Install Fluxomni Studio:

```bash
curl -fsSL https://install.fluxomni.io | bash
```

By default, the installer uses the newest stable release and installs Fluxomni Studio on one server.

Use `FLUXOMNI_VERSION=edge` only when you want the newest main-branch build. Use a canonical public tag like `v26.2.4` when you need a pinned stable release. Retained `v0.x.y` core tags remain available for rollback.

To add a remote media server, run the same installer on that server with `bash -s -- media-node`.

After installation, open `http://<your-server-ip>/routes` and follow [First Stream](getting-started/first-stream.md). It guides you through creating the first admin account, accepting an RTMP source, adding an output, verifying playback, and taking an initial backup.

Choose the next path that matches your goal:

- **Run one stream on one server** — [Quick Start](getting-started/quick-start.md), then [First Stream](getting-started/first-stream.md)
- **Deploy on a cloud provider** — [Deployment](deployment/overview.md)
- **Secure a browser-accessible deployment** — [Reverse Proxy & TLS](getting-started/reverse-proxy.md) or [Private Access & Tunnels](getting-started/private-access.md)
- **Operate routes and media nodes** — [User Guide](user-guide/overview.md)
- **Automate an installation** — [API Automation](api/overview.md)

## Documentation Sections

- [Quick Start](getting-started/quick-start.md) — install Fluxomni Studio
- [First Stream](getting-started/first-stream.md) — create, publish, verify, and protect your first route
- [Deployment](deployment/overview.md) — cloud provider guides and server provisioning
- [User Guide](user-guide/overview.md) — operate the Control Surface, including Attention, Routes, Fleet, and settings
- [Configuration](getting-started/configuration.md) — configure access, networking, and runtime variables
- [Monitoring](getting-started/monitoring.md), [Backup & Restore](getting-started/backup.md), and [Troubleshooting](getting-started/troubleshooting.md) — maintain an installation
- [Scenarios](scenarios/README.md) — choose a guided deployment pattern
- [API Automation](api/overview.md) — session auth, raw GraphQL, TypeScript client, subscriptions, errors, and workflow recipes
- [Changelog](changelog.md) and [Roadmap](roadmap.md) — product updates and direction

## Release Channels

- `latest`: newest stable release
- `vYY.Q.N`: canonical public stable release tag
- `vX.Y.Z`: core image tag, accepted for direct image pinning
- `edge`: latest successful publish from `main`

## Support

- Found an issue? Open it in the [self-host repository issue tracker](https://github.com/fluxomnia-systems/fluxomni-selfhost/issues)
