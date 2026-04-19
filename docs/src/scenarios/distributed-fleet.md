# Distributed fleet with regional failover

## Who this is for

Broadcast-ops teams that need regional redundancy, higher aggregate capacity, or data-locality across regions (e.g. EU vs US). You want one control plane, several media nodes, and automatic ingress failover without operator intervention.

## What you'll build

One control plane and two or more media nodes across regions. Routes assigned via labels/zones. Automatic failover across primary, backup, file-backup, and playlist ingress sources.

```text
Control plane (orchestration + UI)
        │ gRPC
        ├── media-node (zone=eu)
        └── media-node (zone=us)
```

## Setup

1. Install the control plane on the orchestration host: `curl -fsSL https://install.fluxomni.io | bash`.
2. Install a media-node on each regional host. Point it at the control plane with `FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT`. See [Configuration](../getting-started/configuration.md).
3. Label the nodes (`zone=eu`, `zone=us`) from the Fleet view.
4. Assign routes to zones with label selectors. See [Fleet](../user-guide/fleet.md).
5. Configure [ingress failover](../user-guide/routes.md) per route (primary → backup → file-backup → playlist).

## Cost and scale notes

Linear scaling — each node carries its local routes; the control plane hosts only orchestration, not media pipelines. Add a node, label it, assign routes. No changes to publish addresses seen by clients.

## Next steps

- [Fleet — health, assignments, resources](../user-guide/fleet.md)
- [Reverse proxy & TLS](../getting-started/reverse-proxy.md)
- [Backup and restore](../getting-started/backup.md)
