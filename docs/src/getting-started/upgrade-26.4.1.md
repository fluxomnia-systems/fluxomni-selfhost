# Upgrade to 26.4.1

Upgrade the frontend, control plane, and every media node to the same release. 26.4.1 changes how a media node declares its capabilities and reachability, so a node left on 26.4.0 will not match the control plane. Plan a short maintenance window so every node is recreated with the new release before traffic returns.

There is no schema migration in this release, and it does not create a new capacity ledger. The [26.4.0 upgrade](upgrade-26.4.0.md) already initialized the ledger. An installation still on 26.3.x must complete that upgrade first. An existing install still needs a capacity maintenance mode: a plain `bash install.sh` exits before it upgrades.

## Before upgrading

1. Record the current image tags or digests on every host and save the Compose files, overrides, and `.env` files needed to restore them.
2. Take a consistent [backup](backup.md) of state and media that you need to retain. Stop the stack for a filesystem backup, or use SQLite's backup API; copying only a live `state.db` is insufficient.
3. Review node capability settings, described below. A node that relied on a label to grant a capability needs the new environment variable instead.
4. Update custom API consumers as described below. Pin `@fluxomni/api-client@26.4.1` and validate your own operations against the [released GraphQL schema](https://raw.githubusercontent.com/fluxomnia-systems/fluxomni/v26.4.1/api/schema.graphql).

## Node capabilities and reachability

26.4.1 replaces label-based capability grants with explicit settings:

- `FLUXOMNI_MEDIA_NODE_CAPABILITIES` declares `gpu_transcode`, `public_ingest`, and `public_egress`. A label no longer grants any of these.
- `FLUXOMNI_MEDIA_NODE_PRIVATE_NETWORK_ONLY` declares private-network-only reachability. The Fleet API value `TAILNET_ONLY` is now `PRIVATE_NETWORK_ONLY`.
- Node labels are validated: 1 to 70 characters, with no commas or control characters. An invalid non-empty label stops the node at startup and is rejected at registration.
- The FFmpeg toolchain fingerprint moved to its own registration field. A label prefixed with the fingerprint is no longer read.

Set these before recreating each media node. A node that starts with an invalid label will not register.

## Upgrade an installer-managed stack

Pin `v26.4.1` from install.fluxomni.io. `https://install.fluxomni.io/v26.4.1` and `FLUXOMNI_VERSION=v26.4.1` select the same release.

On the control-plane host, disable every route and confirm Fleet shows zero reservations. Then upgrade with the drained mode. The ordered checks are in [Later Planned Upgrades](capacity-upgrades.md#later-planned-upgrades).

```bash
curl -fsSL https://install.fluxomni.io -o /tmp/fluxomni-install.sh
FLUXOMNI_DIR="$HOME/fluxomni" FLUXOMNI_VERSION=v26.4.1 \
  bash /tmp/fluxomni-install.sh full --capacity-upgrade drained
```

The installer keeps data and updates its managed files. It does not guarantee a rolling upgrade without downtime. Keep the existing control-plane endpoint, node identity, and public host settings, and review custom Compose overrides before restarting.

After the control-plane step succeeds, update each standalone media node with the same release, the node maintenance mode, and its capability settings:

```bash
curl -fsSL https://install.fluxomni.io -o /tmp/fluxomni-install.sh
FLUXOMNI_DIR="$HOME/fluxomni-media-node" FLUXOMNI_VERSION=v26.4.1 \
  FLUXOMNI_MEDIA_NODE_CAPABILITIES=public_ingest,public_egress \
  bash /tmp/fluxomni-install.sh media-node --capacity-upgrade node --confirm-control-plane-ready
```

Set `FLUXOMNI_MEDIA_NODE_CAPABILITIES` to the capabilities that node should advertise, and add `FLUXOMNI_MEDIA_NODE_PRIVATE_NETWORK_ONLY` for a node that is reachable only on a private network.

## Upgrade a manual deployment

Manual deployments should pull `v26.4.1` for the frontend, control plane, and every media node, then recreate them together. Set the capability and reachability variables in each media node's environment before starting it.

Images:

- `ghcr.io/fluxomnia-systems/fluxomni-frontend:v26.4.1`
- `ghcr.io/fluxomnia-systems/fluxomni-control-plane:v26.4.1`
- `ghcr.io/fluxomnia-systems/fluxomni-media-node:v26.4.1`

## API changes

`@fluxomni/api-client@26.4.1` matches this release. A package upgrade does not rewrite custom GraphQL strings.

The Fleet reachability value `TAILNET_ONLY` is renamed to `PRIVATE_NETWORK_ONLY`. A query or mutation that sends or matches the old value must use the new one.

`moveOutput` now reports `UNCHANGED` and `NOT_FOUND` correctly, and broadcast play and stop return per-route failures. A client that treated any non-success as a single failure should read the per-route result.

The removals from [26.4.0](upgrade-26.4.0.md#api-changes) still apply: the filename-only DVR query and removal mutation, the legacy `setPassword` mutation, and the requirement that GraphQL HTTP POST requests use `Content-Type: application/json`.

## Verify the upgrade

1. Confirm the running image versions on every host with `docker compose images` and check service health with `docker compose ps`.
2. Open Fleet and confirm that the expected nodes reconnect and report compatible versions. Check that each node shows the capabilities and reachability you set, and that none failed registration on an invalid label.
3. Publish a representative stream, verify preview and each destination receiver, then test a source reconnect.
4. If you use Google Drive, open Artifacts, register a folder source, and run **Check now**. Confirm the scan queues only files the library does not already have, and that a second scan adds nothing.
5. Open Settings as an administrator and confirm the change history lists recent changes with the actor, domain, and outcome filters.
6. Exercise your custom API queries, including any that referenced `TAILNET_ONLY`. Check logs for schema errors, startup failures, and stale heartbeats.
