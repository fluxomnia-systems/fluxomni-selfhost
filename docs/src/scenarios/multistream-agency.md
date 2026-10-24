# Multistream agency

## Who this is for

Agencies and teams streaming for several clients to YouTube, Twitch, Facebook, or custom RTMP destinations. Use one route per client so you can label the work, control its outputs, and export its configuration.

## What you'll build

A single-host Fluxomni Studio install with one route per client. The example relays media without re-encoding it. Size the host for your actual inputs, output count, and bitrate before adding clients.

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

Use the [measured sizing guide](../getting-started/sizing.md) as a starting point, then test your client workload. Count active inputs and destinations separately. Leave capacity for reconnects and other recovery work.

Budget for the server, transfer allowance, storage, and any commercial license. [Contact the team](https://fluxomni.io/contact?intent=business) about licensing for client work. Adding media nodes can distribute work; test placement and publisher connectivity when expanding the fleet.

## Next steps

- [Per-route detail and editing](../user-guide/routes.md)
- [Backup and restore](../getting-started/backup.md)
- [Fleet monitoring](../user-guide/fleet.md)
