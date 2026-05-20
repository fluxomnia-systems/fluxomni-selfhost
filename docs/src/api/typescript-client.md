# TypeScript Client

`@fluxomni/api-client` is a thin session-aware GraphQL transport. It does not hide the schema behind a separate domain SDK.

Install it in your automation project:

```bash
npm install @fluxomni/api-client
```

## Login And Query

```typescript
import { GraphQLClient } from '@fluxomni/api-client';

const { client } = await GraphQLClient.login({
  baseUrl: 'http://<your-server>',
  username: process.env.FLUXOMNI_USERNAME!,
  password: process.env.FLUXOMNI_PASSWORD!,
});

const data = await client.executeRaw<{
  routes: { allRoutes: Array<{ id: string; label?: string | null }> };
}>(`
  query Routes {
    routes {
      allRoutes {
        id
        label
      }
    }
  }
`);

console.log(data.routes.allRoutes);
client.stop();
```

Browser and same-origin callers can omit endpoint options and let the browser manage cookies.

## Generated Operations

The package exports generated GraphQL documents and result types for callers that want compile-time operation typing.

```typescript
import { GraphQLClient, ServerInfoDocument } from '@fluxomni/api-client';

const { client } = await GraphQLClient.login({ username, password });
const data = await client.query({ query: ServerInfoDocument });
client.stop();
```

## Executable Examples

Release examples live in the main Fluxomni repository under `api/examples/typescript`.

They cover:

- session login plus raw query/subscription
- route desired-state convergence
- publish credential, source preference, failover, and output controls
- playlist, artifact tags, settings export/import, Fleet health, and guarded Fleet commands

In a Fluxomni source checkout, compile them with:

```bash
pnpm --filter @fluxomni/api-client run examples:check
```
