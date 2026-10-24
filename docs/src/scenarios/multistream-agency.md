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

For clients using the same copy-mode workload as the [sizing guide](../getting-started/sizing.md), these examples give a starting media budget:

| Active client routes | Outputs per client | Total outputs | Media CPU / RAM budget | Basis |
| --- | --- | --- | --- | --- |
| 4 | 12 | 48 | 1 CPU / 2 GiB | Measured media workload |
| 8 | 12 | 96 | 2 CPUs / 4 GiB | 2× extrapolation |
| 16 | 12 | 192 | 4 CPUs / 8 GiB | 4× extrapolation |

The measured workload used about 2.646 Mbit/s per output. The larger rows assume comparable CPU performance and the same bitrate and fan-out. Add resources for the rest of the stack, then test your client streams and recovery load before setting a client limit.

Budget for the server, transfer allowance, storage, and any commercial license. [Contact the team](https://fluxomni.io/contact?intent=business) about licensing for client work. Adding media nodes can distribute work; test placement and publisher connectivity when expanding the fleet.

## Next steps

- [Per-route detail and editing](../user-guide/routes.md)
- [Backup and restore](../getting-started/backup.md)
- [Fleet monitoring](../user-guide/fleet.md)
