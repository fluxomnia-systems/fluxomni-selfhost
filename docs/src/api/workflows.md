# Automation Workflows

Good automation follows a desired-state loop: read current state, compute a change, apply a public mutation, then re-read or subscribe until the expected state appears.

## Route Desired State

Use `routes.allRoutes` to inspect current route topology and presentation. Use `routes.setRoute` to create or update route identity and route-source topology, then `routes.setOutput` for output destinations.

Key result payloads:

- `RouteMutationResult { status, routeId }`
- `RouteSourceMutationResult { status, routeId, sourceId }`
- `OutputMutationResult { status, routeId, outputId }`

The executable `ensure-route-desired-state.ts` example in the Fluxomni source repo demonstrates this loop.

## Route Controls

Public route-control workflows include:

- rotate or revoke a route-source publish credential
- prefer or clear a route source
- adjust source failover policy
- enable, disable, reorder, or remove outputs

The `manage-route-controls.ts` example covers these operations.

## Playlists, Artifacts, And Settings

Public automation can:

- set playlist queue order
- enable sequential playback
- tag reusable library artifacts
- export settings
- import a controlled route spec

Use `LibraryFile` rows as durable artifact catalog records. Runtime file-state rows are for observation and troubleshooting.

The `manage-playlist-artifacts-settings-fleet.ts` example covers these flows.

## Fleet Commands

Fleet command mutations are exceptional operator actions, not ordinary toggles.

Public commands:

- `fleet.drainMediaNode(nodeId)`
- `fleet.enterMediaNodeMaintenance(nodeId)`
- `fleet.exitMediaNodeMaintenance(nodeId)`
- `fleet.removeMediaNode(nodeId)`

Always preflight `fleet.mediaNodes` before issuing a command. Check the target node, `state`, `operatorStateOverride`, `acceptsNewWork`, `assignedRouteCount`, and assigned route manifest delivery state.

After a command, re-read `fleet.mediaNodes` and confirm convergence:

- draining or maintenance nodes should stop accepting new work
- exiting maintenance should clear `operatorStateOverride`
- removing a node should remove it from `fleet.mediaNodes`

Do not retry exceptional Fleet commands in a tight loop. Re-read Fleet state, compare it with your intended precondition, and retry only if the observed state still justifies the command.
