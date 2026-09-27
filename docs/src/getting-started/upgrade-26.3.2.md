# Upgrade to 26.3.2

Upgrade the frontend, control plane, and every media node to the same release. Custom GraphQL clients must adopt library pagination and scoped file subscriptions. Plan a maintenance window for active media workloads.

## Before upgrading

1. Record the current image tags or digests on every host and save the Compose files, overrides, and `.env` files needed to restore them.
2. Take a consistent [backup](backup.md) of state and media that you need to retain. Stop the stack for a filesystem backup, or use SQLite's backup API; copying only a live `state.db` is insufficient.
3. Update custom API consumers as described below. Pin `@fluxomni/api-client@26.3.2` and validate your own operations against the [released GraphQL schema](../api/schema.graphql).
4. Review your RTMP, SRT, and WebRTC smoke checks. This release bundles pinned SRS 7.0.165, an upstream alpha build containing the admission-race fix.

## Upgrade an installer-managed stack

Run on the control-plane host, using your existing installation directory:

```bash
curl -fsSL https://install.fluxomni.io -o /tmp/fluxomni-install.sh
FLUXOMNI_DIR="$HOME/fluxomni" FLUXOMNI_VERSION=v26.3.2 \
  bash /tmp/fluxomni-install.sh
```

For each standalone media-node host, use its existing directory and installation mode:

```bash
curl -fsSL https://install.fluxomni.io -o /tmp/fluxomni-install.sh
FLUXOMNI_DIR="$HOME/fluxomni-media-node" FLUXOMNI_VERSION=v26.3.2 \
  bash /tmp/fluxomni-install.sh media-node
```

Keep the existing control-plane endpoint, internal authentication token, node identity, and public host settings. Review custom Compose overrides before restarting. The installer preserves data and updates its managed files; it is not a zero-downtime rolling-upgrade guarantee. Manual deployments should update all three image tags to `v26.3.2`, pull them, and recreate the services using their existing configuration.

## API changes

`artifacts.libraryFiles` now returns `nodes`, `totalCount`, `hasNextPage`, and `endCursor`. The default page contains up to 50 files; `first` accepts 1–200. Filters and sorting apply across the catalog, not only the current page.

```graphql
query LibraryPage($after: String) {
  artifacts {
    libraryFiles(first: 50, after: $after, sort: NAME) {
      nodes { id name }
      totalCount
      hasNextPage
      endCursor
    }
  }
}
```

Start with `after: null`. Process `nodes`; while `hasNextPage` is true, send the returned `endCursor` as `after`. Reset the cursor when filters or sorting change. Do not treat the first page as the whole library or assume pagination is a snapshot of a concurrently changing catalog.

Replace the removed `artifacts` subscription with the scope your consumer needs:

- `fileTransfers`: active and failed transfers; completed library files are excluded.
- `routeFiles(routeId: ...)`: files referenced by one visible route's playlist and file sources.
- `file(fileId: ...)`: changes to one file, with a nullable result.

Use paginated queries for library listings. Unsubscribe when a consumer leaves a route or stops watching a file, and stop the client at shutdown. See [subscriptions](../api/subscriptions.md) for examples. A package upgrade alone does not rewrite custom GraphQL strings.

## Verify the upgrade

1. Confirm the running image versions on every host with `docker compose images` and check service health with `docker compose ps`.
2. Open Fleet and confirm that the expected nodes reconnect, report compatible versions, and receive their route assignments.
3. Publish a representative stream, verify preview and each destination receiver, then test a source reconnect. An output's LIVE state now requires FFmpeg progress; receiver playback remains the end-to-end check.
4. Open Artifacts, move beyond the first page, and exercise your custom API queries and subscriptions. Check logs for schema errors, startup failures, and stale heartbeats.
5. Compare CPU, memory, and network use under your actual workload with the [sizing guidance](sizing.md). Empty-route measurements do not predict active-stream capacity.

If verification fails, stop the changed stack, restore the saved configuration and a consistent pre-upgrade data backup, and recreate the previous pinned images on all hosts. Retain diagnostic logs first. Do not assume a previous binary can safely run against state already changed by a newer release.
