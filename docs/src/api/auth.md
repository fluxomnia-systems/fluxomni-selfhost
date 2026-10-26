# API Authentication

GraphQL HTTP and WebSocket requests use named-user browser sessions. The configured sign-in mode determines how those sessions are created.

Without browser OIDC, `/api/auth/login` accepts the local username and password. Keep its returned `fluxomni_session` cookie and send it with GraphQL HTTP and WebSocket subscription requests.

With browser OIDC configured, sign in through the configured issuer in the operator UI. `/api/auth/login` cannot create a password session in that mode. See [unified sign-in and account enrollment](mcp.md#enroll-an-existing-local-account). The verified callback creates an opaque Fluxomni browser cookie; issuer email and role claims do not choose the local account or its permissions.

MCP OAuth credentials work only at the configured MCP resource. They cannot authorize ordinary GraphQL or WebSocket requests. MCP approvals are read-only by default. An optional management scope and explicit client management approval allow [route, library, playlist and output changes](mcp.md#optional-management-access) within the current user and route permissions. No service-account credential is added.

## Login

This password login example applies only when browser OIDC is not configured.

```bash
curl -i \
  -H 'content-type: application/json' \
  -d '{"username":"admin","password":"your-password"}' \
  http://<your-server>/api/auth/login
```

The response sets a `fluxomni_session` cookie when the credentials are valid.

Use `/api/auth/status` to check the current session:

```bash
curl -b "fluxomni_session=$SESSION" \
  http://<your-server>/api/auth/status
```

## Roles

Automation uses the same role permissions as the UI:

- **Admin** — full access to routes, artifacts, Fleet, settings, user management, export/import, and ownership assignment.
- **Operator** — can manage visible routes, sources, outputs, playlists, and artifacts, plus self-service settings.
- **Viewer** — read-only access to visible routes and system surfaces.

## Session Expiry

Session lifetime is controlled by the server `sessionTtlSeconds` setting. A value of `0` or `null` disables expiry. Other values set the number of seconds from login until the in-memory session expires.

Treat HTTP `401` or GraphQL `extensions.code: "UNAUTHORIZED"` as a signal to authenticate again using the configured mode. Issuer sessions and browser cookies have separate lifetimes; an expired cookie needs a new verified browser sign-in. Provider account changes do not independently revoke an already issued Fluxomni cookie; local revision changes, configured expiry or explicit local sign-out do.

Use explicit [MCP client approval](mcp.md#sign-in-and-approve-a-client) for automation on an issuer-configured instance. Read access and optional management access require their own configured scopes and approved client permissions. Browser sign-in never creates that approval automatically.

## Internal Credentials

Loopback bearer authentication is for internal control-plane and media-node traffic only. Do not use `Authorization: Bearer` as a public automation credential.
