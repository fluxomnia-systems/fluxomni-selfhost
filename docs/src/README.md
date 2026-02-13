# FluxOmni

<p align="center">
  <img src="images/logo.webp" alt="FluxOmni Logo" width="10%">
</p>

FluxOmni is a web-based RTMP streaming platform for broadcasting one source to multiple destinations.

This repository contains self-host installation and deployment documentation only.

## Quick Start

Install FluxOmni in one command:

```bash
curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh | bash
```

After installation:

- Web UI: `http://<your-server-ip>`
- RTMP ingest: `rtmp://<your-server-ip>:1935/app`

## Documentation Sections

- [Quick Start](getting-started/quick-start.md)
- [Configuration](getting-started/configuration.md)
- [Cloud Deployment Guides](deployment/)
- [Server Provisioning Script](deployment/provision.md)

## Support

- Found an issue? Open it in the [self-host repository issue tracker](https://github.com/fluxomnia-systems/fluxomni-selfhost/issues)
