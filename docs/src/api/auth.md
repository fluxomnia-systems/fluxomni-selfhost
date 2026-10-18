# API Authentication

API automation uses the same named-user sessions as the operator UI.

Log in with `/api/auth/login`, keep the returned `fluxomni_session` cookie, and send it with GraphQL HTTP and WebSocket subscription requests.

## Login

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

Scripts should treat HTTP `401` or GraphQL `extensions.code: "UNAUTHORIZED"` as a signal to log in again.

## Internal Credentials

Loopback bearer authentication is for internal control-plane and media-node traffic only. Do not use `Authorization: Bearer` as a public automation credential.
