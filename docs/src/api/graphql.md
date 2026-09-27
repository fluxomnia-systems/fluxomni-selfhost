# Raw GraphQL

Fluxomni Studio accepts GraphQL HTTP POST requests at `/api`.

Raw GraphQL is the most portable automation format because it maps directly to the release schema.

## Query

```bash
curl \
  -b "fluxomni_session=$SESSION" \
  -H 'content-type: application/json' \
  -d '{"query":"query Routes { routes { allRoutes { id label enabled presentation { phase label } } } }"}' \
  http://<your-server>/api
```

## Mutation

Mutation payloads expose machine-readable status values when no-op or missing-target outcomes are normal convergence states.

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

Use the release-tagged `api/schema.graphql` from GitHub when pinning automation to a specific Fluxomni Studio release.

## Library Pagination

In 26.3.2, `artifacts.libraryFiles` returns a page object. Select its `nodes` and follow `endCursor` while `hasNextPage` is true. The default page size is 50, with a maximum of 200. See the [upgrade guide's executable query](../getting-started/upgrade-26.3.2.md#api-changes).
