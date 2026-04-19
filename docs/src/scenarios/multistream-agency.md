# Multistream agency

## Who this is for

Agencies and teams operating multistreaming ops on behalf of clients — typically 10–50 concurrent routes across YouTube, Twitch, Facebook, and custom RTMP destinations. You want predictable per-month cost, clear per-client separation, and the ability to hand a client a stable publish address without exposing your internal infra.

## What you'll build

Single-host FluxOmni on a modest cloud VM serving dozens of copy-through routes — one per client brand — with per-route labels and exported configs ready to migrate to a multi-node fleet when load grows.

```text
1 OBS per client → FluxOmni single-host → fan-out to { YouTube, Twitch, Custom RTMP }
```

## Setup

1. Provision a *nix server. See [Deployment guides](../deployment/overview.md).
2. Install with `curl -fsSL https://install.fluxomni.io | bash`.
3. Open the control surface and create a route per client. Use the `label` field for the client name.
4. Configure outputs per platform. Use [per-route controls](../user-guide/routes.md) to start/stop by client.
5. Export configs with the `Export` button — check them into your ops repo for disaster recovery.

## Cost and scale notes

A Hetzner CPX31 (4 vCPU / 8 GB / ~€15 per month) comfortably carries ~70 copy-through routes. A CPX41 (8 vCPU / 16 GB / ~€29 per month) handles 100+. Scale further by adding media nodes — no need to migrate routes or change client publish addresses.

## Next steps

- [Per-route detail and editing](../user-guide/routes.md)
- [Backup and restore](../getting-started/backup.md)
- [Fleet monitoring](../user-guide/fleet.md)
