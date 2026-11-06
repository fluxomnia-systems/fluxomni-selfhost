# Upgrade to 26.4.0

Upgrade the frontend, control plane, and every media node to the same release. v26.4.0 initializes the per-node capacity ledger and migrates operational state into the released relational schema. Plan a maintenance window for active media workloads.

## Before upgrading

1. Record the current image tags or digests on every host and save the Compose files, overrides, and `.env` files needed to restore them.
2. Take a consistent [backup](backup.md) of state and media that you need to retain. Stop the stack for a filesystem backup, or use SQLite's backup API; copying only a live `state.db` is insufficient.
3. Update custom API consumers as described below. Pin `@fluxomni/api-client@26.4.0` and validate your own operations against the [released GraphQL schema](https://raw.githubusercontent.com/fluxomnia-systems/fluxomni/v26.4.0/api/schema.graphql).
4. If you are moving from v26.3.x and any route or output execution is running or assigned, the [first capacity upgrade](capacity-upgrades.md#first-capacity-upgrade) is required before media starts on this release. Stop every old execution container, then initialize the ledger. Later restarts keep execution ownership.
5. Reverse-proxy deployments must set `FLUXOMNI_TRUSTED_PROXY_IPS` to the exact proxy IPs. Proxies must append or replace client-address headers. Without that setting, clients behind a proxy share one login limit. See [Reverse Proxy & TLS](reverse-proxy.md#client-address).

One SQLite baseline handles fresh installs and direct upgrades from released schema 11. Existing data is kept. Do not start a v26.3.x binary on a database this release has migrated.

## Upgrade an installer-managed stack

Pin `v26.4.0` from install.fluxomni.io. `https://install.fluxomni.io/v26.4.0` and `FLUXOMNI_VERSION=v26.4.0` select the same release.

An established installation, including any move from v26.3.x that still has running or assigned execution, must use the capacity maintenance flags. Stop every external execution container first. The ordered checks, failure behavior, and retry rules are in [Capacity Ledger Upgrades](capacity-upgrades.md). On the control-plane host:

```bash
curl -fsSL https://install.fluxomni.io -o /tmp/fluxomni-install.sh
FLUXOMNI_DIR="$HOME/fluxomni" FLUXOMNI_VERSION=v26.4.0 \
  bash /tmp/fluxomni-install.sh full --capacity-upgrade initial --confirm-execution-stopped
```

`--confirm-execution-stopped` asserts that every external predecessor execution container and updater is stopped. The installer controls its local node. It cannot inspect other hosts. Do not put `FLUXOMNI_CAPACITY_UPGRADE_STOPPED` in `.env` or pass it as an installer environment variable. The installer applies that acknowledgement only inside initial mode and removes it before starting media.

After the control-plane step succeeds, update each already stopped standalone media node with the same release:

```bash
curl -fsSL https://install.fluxomni.io -o /tmp/fluxomni-install.sh
FLUXOMNI_DIR="$HOME/fluxomni-media-node" FLUXOMNI_VERSION=v26.4.0 \
  bash /tmp/fluxomni-install.sh media-node --capacity-upgrade node --confirm-control-plane-ready
```

A fresh installation with no previous execution can omit the capacity-upgrade flags:

```bash
curl -fsSL https://install.fluxomni.io -o /tmp/fluxomni-install.sh
FLUXOMNI_DIR="$HOME/fluxomni" FLUXOMNI_VERSION=v26.4.0 \
  bash /tmp/fluxomni-install.sh
```

Keep the existing control-plane endpoint, node identity, and public host settings. Review custom Compose overrides before restarting. The installer keeps data and updates its managed files. It does not guarantee a rolling upgrade without downtime.

Manual deployments should pull `v26.4.0` for the frontend, control plane, and every media node, then recreate them together. If execution is already running or assigned, stop the old execution containers and start the control plane once with `FLUXOMNI_CAPACITY_UPGRADE_STOPPED=true`. Remove that variable after a successful start, and do not leave it in `.env`. Start media nodes only after the ledger is initialized and the acknowledgement is gone. Implement the same boundaries as [Capacity Ledger Upgrades](capacity-upgrades.md).

Images:

- `ghcr.io/fluxomnia-systems/fluxomni-frontend:v26.4.0`
- `ghcr.io/fluxomnia-systems/fluxomni-control-plane:v26.4.0`
- `ghcr.io/fluxomnia-systems/fluxomni-media-node:v26.4.0`

## API changes

`@fluxomni/api-client@26.4.0` matches this release. GraphQL HTTP POST requests must use `Content-Type: application/json`. WebSocket connections that do not initialize within ten seconds are closed. A package upgrade does not rewrite custom GraphQL strings.

The filename-only DVR query `artifacts.dvrFiles` and the filename removal mutation `artifacts.removeDvrFile` are removed. List recordings through the artifact library by kind and output ID, and delete them by file ID:

```graphql
query Recordings($after: String, $outputId: String!) {
  artifacts {
    libraryFiles(
      first: 50
      after: $after
      filter: { artifact: { kind: RECORDING, outputId: $outputId } }
    ) {
      nodes { id name }
      totalCount
      hasNextPage
      endCursor
    }
  }
}
```

Delete returned file IDs with `deleteLibraryFiles`. Use `forceDeleteLibraryFiles` only when the existing library API must detach route references first. Pagination rules from [26.3.2](upgrade-26.3.2.md#api-changes) still apply.

The legacy `systemSettings.setPassword` mutation is removed. Create users with `createUser`, rotate the current user's password with `changeMyPassword`, and end sessions with session logout.

Slideshow commands require a `requestId`. `saveSlideshow` takes it on the input. `cancelSlideshow` and `retrySlideshow` take it with the operation ID. A retry of the same request returns the original command receipt. The `slideshow` field on the result is the current record, not the body from the first call.

Library pagination from 26.3.2 is unchanged: `artifacts.libraryFiles` returns `nodes`, `totalCount`, `hasNextPage`, and `endCursor`.

## Verify the upgrade

1. Confirm the running image versions on every host with `docker compose images` and check service health with `docker compose ps`.
2. Open Fleet and confirm that the expected nodes reconnect, report compatible versions, and receive their route assignments. For a private node, confirm control connection state separately from media access.
3. Publish a representative stream, verify preview and each destination receiver, then test a source reconnect.
4. Open Artifacts and check recordings you expect to keep, including a preserved or historical recording when you use DVR. Exercise your custom API queries. Check logs for schema errors, startup failures, and stale heartbeats.
5. When preparation isolation is configured, confirm Fleet shows preparation enforcement and that preparation does not run without it.
6. Compare CPU, memory, and network use under your actual workload with the [sizing guidance](sizing.md). Empty-route measurements do not predict active-stream capacity.

If verification fails, stop the changed stack, restore the saved configuration and a consistent pre-upgrade data backup, and recreate the previous pinned images on all hosts. Save diagnostic logs first. Do not assume a previous binary can safely run against state already changed by this release.
