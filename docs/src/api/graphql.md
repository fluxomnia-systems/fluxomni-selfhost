# Raw GraphQL

Fluxomni accepts GraphQL HTTP POST requests at `/api`.

Raw GraphQL uses the release schema directly and works across languages and clients.

## Query

```bash
curl \
  -b "fluxomni_session=$SESSION" \
  -H 'content-type: application/json' \
  -d '{"query":"query Routes { routes { allRoutes { id label enabled presentation { phase label } } } }"}' \
  http://<your-server>/api
```

## Mutation

Mutation payloads return status values for scripts to check. An operation that changes nothing or finds no target can return a normal result.

```graphql
mutation DisableOutput($routeId: RouteId!, $outputId: OutputId!) {
  routes {
    disableOutput(routeId: $routeId, id: $outputId) {
      status
      routeId
      outputId
    }
  }
}
```

Common status values:

- `UPDATED` — the operation changed or accepted the target state.
- `UNCHANGED` — the requested state was already in effect.
- `NOT_FOUND` — the target was missing and the mutation can express that as a normal result.

GraphQL errors are still used for malformed input, permission failures, persistence failures, runtime-unavailable cases, and rejected exceptional commands.

## Schema

Fetch the running server schema:

```bash
curl -b "fluxomni_session=$SESSION" \
  http://<your-server>/api/schema.graphql
```

Use the release-tagged `api/schema.graphql` from GitHub when pinning automation to a specific Fluxomni release.

## Library Pagination

In 26.3.2, `artifacts.libraryFiles` returns a page object. Select its `nodes` and follow `endCursor` while `hasNextPage` is true. The default page size is 50, with a maximum of 200. See the [26.3.2 upgrade guide](../getting-started/upgrade-26.3.2.md#api-changes).

In 26.4.0, POST requests must use `application/json`. The filename-only DVR query and removal mutation are removed. List recordings with `libraryFiles` filtered by artifact kind `RECORDING` and output ID, and delete them by file ID. Slideshow mutations require a request ID. The legacy `setPassword` mutation is removed. See the [26.4.0 upgrade guide](../getting-started/upgrade-26.4.0.md#api-changes).
