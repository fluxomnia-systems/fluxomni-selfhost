# GraphQL Subscriptions

Subscriptions use `graphql-ws` at `/api/subscriptions`.

They use the same session identity as GraphQL HTTP.

## Server-Side Clients

Server-side scripts should pass the login cookie through the WebSocket `connection_init` payload.

`GraphQLClient.login()` handles this when you provide a WebSocket endpoint:

```typescript
import { GraphQLClient, StateDocument } from '@fluxomni/api-client';

const { client } = await GraphQLClient.login({
  baseUrl: 'http://<your-server>',
  username: process.env.FLUXOMNI_USERNAME!,
  password: process.env.FLUXOMNI_PASSWORD!,
  wsEndpoint: 'ws://<your-server>/api/subscriptions',
});

const sub = client.subscribe({ query: StateDocument }).subscribe({
  next: (result) => console.log(result.data?.allRoutes.length),
  error: (error) => console.error(error),
});

setTimeout(() => {
  sub.unsubscribe();
  client.stop();
}, 5000);
```

## Browser Clients

Browsers normally manage same-origin cookies. Keep browser-specific setup in the web app. Use the API client to send and receive data, and manage UI state in the app.

## Public Subscription Fields

Use subscriptions to observe the same workflow state documented by queries:

- `allRoutes`
- `routeWithParent`
- `output`
- `fileTransfers`
- `routeFiles(routeId: ...)`
- `file(fileId: ...)`
- `currentlyPlayingFile`
- `info`
- `mediaNodes`

Use runtime and diagnostic subscriptions for troubleshooting. Do not use their results as persistent desired-state records.

## Scoped File Updates

In 26.3.2, the full-catalog `artifacts` subscription is removed. Use a paginated query for library browsing, `fileTransfers` for active or failed downloads, or a route/file subscription when the client needs only one route or file.

```graphql
subscription RouteFiles($routeId: RouteId!) {
  routeFiles(routeId: $routeId) { fileId state }
}
```

```graphql
subscription FileState($fileId: FileId!) {
  file(fileId: $fileId) { fileId state }
}
```

A single-file result can be null. Route subscriptions require visibility of that route. Unsubscribe when leaving a route or file. Unused subscriptions still create server work. See the [upgrade guide](../getting-started/upgrade-26.3.2.md#api-changes) for pagination and migration details.
