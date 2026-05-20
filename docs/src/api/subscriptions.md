# GraphQL Subscriptions

Subscriptions use `graphql-ws` at `/api/subscriptions`.

They authenticate with the same session principal as GraphQL HTTP.

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

Browser callers normally rely on same-origin cookie handling. Keep browser-specific wiring in the webapp boundary and use the API client as transport, not as UI state.

## Public Subscription Fields

Use subscriptions to observe the same workflow state documented by queries:

- `allRoutes`
- `routeWithParent`
- `output`
- `currentlyPlayingFile`
- `info`
- `mediaNodes`

Runtime or diagnostic subscriptions can help troubleshooting, but they are not the durable desired-state contract.
