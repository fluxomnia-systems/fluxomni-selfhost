# API Automation

Fluxomni Studio exposes a public API preview for operators who want to automate route, playlist, artifact, settings, and Fleet workflows.

The supported automation surface is GraphQL over `/api`, subscriptions over `/api/subscriptions`, the generated SDL at `/api/schema.graphql`, and the `@fluxomni/api-client` TypeScript package.

Use the API for control-plane automation:

- read route, source, output, playlist, artifact, settings, and Fleet state
- compute the desired state outside Fluxomni Studio
- apply mutations with explicit result payloads
- handle no-op, missing-target, validation, forbidden, and runtime-unavailable outcomes
- observe convergence through follow-up queries or subscriptions

The first stable automation release uses user sessions. Public automation should log in through `/api/auth/login` and reuse the returned `fluxomni_session` cookie. Loopback bearer tokens are internal-only and should not be used by external scripts.

## Versioned Contract

For a running instance, authenticated operators can fetch the active schema:

```bash
curl -b "fluxomni_session=$SESSION" \
  http://<your-server>/api/schema.graphql
```

For release-pinned automation, use the schema and client from the same release tag:

- `https://github.com/fluxomnia-systems/fluxomni/blob/vX.Y.Z/api/schema.graphql`
- `https://github.com/fluxomnia-systems/fluxomni/tree/vX.Y.Z/api/clients/typescript`
- `https://github.com/fluxomnia-systems/fluxomni/tree/vX.Y.Z/api/examples/typescript`

## Supported Fields

Public guides document the compatibility-managed automation surface. Some authenticated GraphQL fields are diagnostic: useful for dashboards and troubleshooting, but not the durable desired-state contract.

Do not build public automation around:

- loopback `Authorization: Bearer` credentials
- `SystemSettingsMutation.setPassword`
- media-node lifecycle ownership or private runtime protocols
- legacy stream/restream route aliases
- diagnostic runtime rows as durable desired-state records

For durable artifact automation, prefer `LibraryFile` catalog rows. Runtime file-state rows are diagnostic.

For route automation, use the route, route source, output, playlist, artifact, settings, and Fleet names shown in the schema and examples.
