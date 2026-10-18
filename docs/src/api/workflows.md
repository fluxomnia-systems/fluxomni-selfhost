# Automation Workflows

Use a desired-state loop for automation: read the current state, calculate a change, apply a public mutation, then query again or subscribe until the expected state appears.

## Route Desired State

Use `routes.allRoutes` to inspect route structure and presentation. Use `routes.setRoute` to create or update route identity and sources. Use `routes.setOutput` for output destinations.

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

Fleet command mutations are special operator actions. Check the current node state before using them.

Public commands:

- `fleet.drainMediaNode(nodeId)`
- `fleet.enterMediaNodeMaintenance(nodeId)`
- `fleet.exitMediaNodeMaintenance(nodeId)`
- `fleet.removeMediaNode(nodeId)`

Always query `fleet.mediaNodes` before issuing a command. Check the target node, `state`, `operatorStateOverride`, `acceptsNewWork`, `assignedRouteCount`, and assigned route manifest delivery state.

After a command, query `fleet.mediaNodes` again and check the result:

- draining or maintenance nodes should stop accepting new work
- exiting maintenance should clear `operatorStateOverride`
- removing a node should remove it from `fleet.mediaNodes`

Do not repeat Fleet commands rapidly. Read Fleet state again and check that it still meets the command's preconditions before retrying.
