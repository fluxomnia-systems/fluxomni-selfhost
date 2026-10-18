# API Automation

Fluxomni Studio provides a public API preview for automating routes, playlists, artifacts, settings, and Fleet tasks.

Use GraphQL at `/api` and subscriptions at `/api/subscriptions`. The API also provides the generated SDL at `/api/schema.graphql`, a bundled [release schema](schema.graphql), [automation recipes](automation-recipes.json), [LLM metadata](llms.txt), and the `@fluxomni/api-client` TypeScript package.

Use the API for control-plane automation:

- read route, source, output, playlist, artifact, settings, and Fleet state
- compute the desired state outside Fluxomni Studio
- apply mutations with explicit result payloads
- handle no-op, missing-target, validation, forbidden, and runtime-unavailable outcomes
- use follow-up queries or subscriptions to check when the expected state is reached

The first stable automation release uses user sessions. Public automation should log in through `/api/auth/login` and reuse the returned `fluxomni_session` cookie. Loopback bearer tokens are internal-only and should not be used by external scripts.

## Versioned Contract

For a running instance, authenticated operators can fetch the active schema:

```bash
curl -b "fluxomni_session=$SESSION" \
  http://<your-server>/api/schema.graphql
```

For release-pinned automation, use the schema, release manifest, and client from the same self-host docs release tag:

- [Bundled GraphQL schema for this docs build](schema.graphql)
- [Automation recipes JSON for this docs build](automation-recipes.json)
- [LLM-readable API metadata for this docs build](llms.txt)
- [Release manifest for matching schema and client versions](../release-manifest.json)
- `https://github.com/fluxomnia-systems/fluxomni-selfhost/blob/vYY.Q.N/docs/src/api/schema.graphql`

## Supported Fields

The public guides describe the API covered by compatibility support. Some authenticated GraphQL fields are for diagnostics, dashboards, and troubleshooting. Do not use them as persistent desired-state records.

Do not build public automation around:

- loopback `Authorization: Bearer` credentials
- `SystemSettingsMutation.setPassword`
- media-node lifecycle ownership or private runtime protocols
- legacy stream/restream route aliases
- diagnostic runtime rows as persistent desired-state records

For durable artifact automation, prefer `LibraryFile` catalog rows. Runtime file-state rows are diagnostic.

For route automation, use the route, route source, output, playlist, artifact, settings, and Fleet names shown in the schema and examples.
