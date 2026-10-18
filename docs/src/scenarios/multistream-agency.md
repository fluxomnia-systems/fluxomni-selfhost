# Multistream agency

## Who this is for

Agencies and teams that stream for clients, typically with 10–50 concurrent routes across YouTube, Twitch, Facebook, and custom RTMP destinations. Use a stable publish address for each client, keep clients separate, and control monthly costs without exposing internal infrastructure.

## What you'll build

A single-host Fluxomni Studio install on a small cloud VM with dozens of copy-through routes, one per client brand. Route labels and exported configurations let you move to a multi-node fleet when load grows.

```text
1 OBS per client → Fluxomni Studio single-host → fan-out to { YouTube, Twitch, Custom RTMP }
```

## Setup

1. Provision a Linux or macOS host. See [Deployment guides](../deployment/overview.md).
2. Install with `curl -fsSL https://install.fluxomni.io | bash`.
3. Open the control surface and create a route per client. Use the `label` field for the client name.
4. Configure outputs per platform. Use [per-route controls](../user-guide/routes.md) to start/stop by client.
5. Export configurations with the `Export` button. Save them in your operations repository for disaster recovery.

## Cost and scale notes

A Hetzner CPX31 (4 vCPU / 8 GB / ~€15 per month) can run ~70 copy-through routes. A CPX41 (8 vCPU / 16 GB / ~€29 per month) handles 100+. Add media nodes for more capacity. You do not need to migrate routes or change client publish addresses.

## Next steps

- [Per-route detail and editing](../user-guide/routes.md)
- [Backup and restore](../getting-started/backup.md)
- [Fleet monitoring](../user-guide/fleet.md)
