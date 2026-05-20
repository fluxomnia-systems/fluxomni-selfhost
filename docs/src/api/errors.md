# Error Handling

Automation should handle GraphQL failures by category. Do not branch on human-readable error messages.

GraphQL errors include `extensions.code` and may include `extensions.status`.

## Categories

- `unauthenticated` — no valid session is attached. Log in again and retry.
- `forbidden` — the session is valid, but the user role cannot access the resolver or object.
- `validation` — the input shape or value is not acceptable.
- `not_found` — the requested route, source, output, artifact, node, user, or settings target does not exist.
- `conflict` — the requested state conflicts with current durable state, ownership, or command preconditions.
- `persistence_failure` — a durable write failed.
- `runtime_unavailable` — runtime state needed by the resolver is not readable right now.
- `operation_rejected` — an exceptional operation, such as a Fleet command, was rejected or could not be safely applied.
- `unknown` — the client could not classify the server code.

Representative codes:

- `UNAUTHORIZED` maps to `unauthenticated`.
- `FORBIDDEN` maps to `forbidden`.
- `INVALID_USERNAME`, `INVALID_SPEC`, `EMPTY_PASSWORD`, and status `400` map to `validation`.
- `ROUTE_NOT_FOUND`, `FILE_NOT_FOUND`, `USER_NOT_FOUND`, and status `404` map to `not_found`.
- `DUPLICATE_ROUTE_NAME`, `FIRST_USER_MUST_BE_ADMIN`, `LAST_ADMIN_REQUIRED`, and status `409` map to `conflict`.
- `FILE_PERSISTENCE_FAILED`, `FILE_TAG_PERSISTENCE_FAILED`, and `USER_PERSISTENCE_FAILED` map to `persistence_failure`.
- `PLAYLIST_RUNTIME_STATE_UNAVAILABLE` and `OUTPUT_RUNTIME_STATE_UNAVAILABLE` map to `runtime_unavailable`.
- `STALE_ASSIGNMENT` and rejected Fleet command codes map to `operation_rejected`.

## TypeScript Classification

```typescript
import { GraphQLError, classifyGraphQLError } from '@fluxomni/api-client';

try {
  await client.executeRaw('query Routes { routes { allRoutes { id } } }');
} catch (error) {
  if (error instanceof GraphQLError) {
    for (const serverError of error.errors) {
      switch (classifyGraphQLError(serverError)) {
        case 'unauthenticated':
          throw new Error('Session expired; log in again.');
        case 'forbidden':
          throw new Error('The current role cannot run this operation.');
        case 'not_found':
          console.warn('Target was already absent:', serverError.code);
          break;
        default:
          throw error;
      }
    }
  }
}
```

Mutation result payloads are not exceptions. Treat `UPDATED`, `UNCHANGED`, and `NOT_FOUND` as normal convergence outcomes when the schema returns a result payload.
