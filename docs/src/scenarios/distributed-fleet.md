# Distributed fleet with regional failover

## Who this is for

Broadcast teams that need media nodes in several regions or more capacity than one server can provide. One control plane manages the fleet. Source failover and recovery after node loss are separate cases to test.

## What you'll build

One control plane and two or more media nodes in different regions. Labels and zones control route placement. Ingress can fail over automatically between primary, backup, file-backup, and playlist sources.

```text
Control plane (orchestration + UI)
        │ gRPC
        ├── media-node (zone=eu)
        └── media-node (zone=us)
```

## Setup

1. Install the control plane on the server that will manage the fleet: `curl -fsSL https://install.fluxomni.io | bash`.
2. Install a media-node on each regional host. Point it at the control plane with `FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT`. See [Configuration](../getting-started/configuration.md).
3. Set each node's `FLUXOMNI_MEDIA_NODE_LABELS` and `FLUXOMNI_MEDIA_NODE_ZONE` when installing it, then confirm the advertised labels and zone in [Fleet](../user-guide/fleet.md).
4. Set route placement in **Advanced routing** when a route must use a specific media node. See [Routes](../user-guide/routes.md#advanced-routing).
5. Configure [ingress failover](../user-guide/routes.md) per route (primary → backup → file-backup → playlist).

## Cost and scale notes

Each node processes its assigned routes. Adding nodes distributes media work, but does not prove linear scaling or remove shared control-plane and network limits. Use the [sizing guide](../getting-started/sizing.md) to plan a load test.

Automatic source failover selects an available source for a route. It does not by itself prove that publishers can reconnect after losing a node. Test node loss, media availability, and publisher connectivity in your own deployment.

## Next steps

- [Fleet — health, assignments, resources](../user-guide/fleet.md)
- [Reverse proxy & TLS](../getting-started/reverse-proxy.md)
- [Backup and restore](../getting-started/backup.md)
