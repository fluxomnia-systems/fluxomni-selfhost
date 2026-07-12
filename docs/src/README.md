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

After installation:

- Open Fluxomni Studio: `http://<your-server-ip>`
- Manage streams: `http://<your-server-ip>/routes`
- Check server health: `http://<your-server-ip>/fleet`
- Publish RTMP: copy the publish address from the [route workspace](user-guide/routes.md#route-workspace)

## Documentation Sections

- [Changelog](changelog.md) — what's new in each release
- [Roadmap](roadmap.md) — current capabilities and product direction
- [Quick Start](getting-started/quick-start.md)
- [Configuration](getting-started/configuration.md)
- [Private Access & Tunnels](getting-started/private-access.md) — Tailscale and Cloudflare Tunnel setup examples
- [Troubleshooting](getting-started/troubleshooting.md)
- [User Guide](user-guide/overview.md) — operating the Control Surface
- [API Automation](api/overview.md) — session auth, raw GraphQL, TypeScript client, subscriptions, errors, and workflow recipes
- [Deployment](deployment/overview.md) — cloud provider guides and server provisioning

## Release Channels

- `latest`: newest stable release
- `vYY.Q.N`: canonical public stable release tag
- `vX.Y.Z`: core image tag, accepted for direct image pinning
- `edge`: latest successful publish from `main`

## Support

- Found an issue? Open it in the [self-host repository issue tracker](https://github.com/fluxomnia-systems/fluxomni-selfhost/issues)
