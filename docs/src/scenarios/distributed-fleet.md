# Distributed fleet with regional failover

## Who this is for

Broadcast teams that need regional redundancy, more total capacity, or data kept in specific regions, such as the EU or US. Use one control plane, several media nodes, and automatic ingress failover without manual action.

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

Capacity grows in proportion to the number of nodes. Each node processes its assigned routes. The control plane manages the fleet without running media pipelines. To add capacity, add a node, label it, and assign routes. Client publish addresses stay the same.

## Next steps

- [Fleet — health, assignments, resources](../user-guide/fleet.md)
- [Reverse proxy & TLS](../getting-started/reverse-proxy.md)
- [Backup and restore](../getting-started/backup.md)
