# Native MCP access

Use native MCP to ask a client for your current user, visible routes and selected-flow readiness. Fluxomni keeps the client read-only and applies your current role plus an independent local approval.

This is a preview integration. It requires a Fluxomni build containing [the native MCP runtime](https://github.com/fluxomnia-systems/fluxomni/pull/437), including its matching frontend. Stable 26.3.2 alone does not provide this feature. The isolated issuer and Codex CLI workflow are verified; an actual web-chat connection remains an acceptance gate.

## Prepare the instance

Use the same public HTTPS origin for the operator UI and MCP resource, for example `https://stream.example.com/mcp`. Run a separate HTTPS issuer, for example `https://auth.example.com/realms/fluxomni`.

You need:

- A reviewed Fluxomni source checkout matching the deployed control plane and frontend.
- PostgreSQL and the normal production TLS configuration for the separate issuer.
- A local named Fluxomni user and a separate issuer account.
- The exact callback URLs reported by the local client and web connection.
- The inspection scope and three tool names agreed for your installation.

The endpoint, scope, tool names and client IDs are deployment inputs. Examples in this guide do not establish a default product catalog. Keep the two client IDs distinct.

Follow [the normal maintenance procedure](../getting-started/capacity-upgrades.md) before recreating an existing control plane. This guide does not change media-node admission or publish ports.

## Build the pinned issuer

Build the issuer extension from the same reviewed Fluxomni source ref as the application:

```bash
docker build \
  --tag fluxomni-mcp-issuer:reviewed \
  /absolute/path/to/fluxomni/deploy/mcp-issuer
```

The Dockerfile pins Keycloak 26.8.1 and its Java compiler by digest. The extension uses supported token post-processing and introspection interfaces. Its `resource-indicators` feature is enabled explicitly and is experimental in this issuer version. Requalify the integration before upgrading the issuer.

Use Keycloak's production PostgreSQL configuration. Preserve and back up that database: it owns issuer users, signing keys, sessions and token lifecycle. Fluxomni's separate SQLite database owns local bindings and approval generations. Keep both owners in your backup plan.

## Generate private settings

Choose an absolute output directory outside the Fluxomni checkout. The directory must not already exist. The generator creates it with owner-only access.

Set the values below to your actual installation. The three tool names are ordered as context, route listing and readiness. For Codex, an explicit loopback callback port must match its configured listener port.

```bash
MCP_ISSUER=https://auth.example.com/realms/fluxomni
MCP_RESOURCE=https://stream.example.com/mcp
MCP_SETUP_DIR=/absolute/private/path/fluxomni-mcp
MCP_SCOPE=your-approved-inspection-scope
MCP_CONTEXT_TOOL=your_context_tool
MCP_ROUTES_TOOL=your_routes_tool
MCP_READINESS_TOOL=your_readiness_tool
MCP_WEB_CALLBACK=https://chatgpt.com/connector_platform_oauth_redirect

python3 /absolute/path/to/fluxomni/scripts/mcp_issuer_setup.py \
  --issuer "$MCP_ISSUER" \
  --resource "$MCP_RESOURCE" \
  --scope "$MCP_SCOPE" \
  --tool-names "$MCP_CONTEXT_TOOL" "$MCP_ROUTES_TOOL" "$MCP_READINESS_TOOL" \
  --local-client-id fluxomni-codex \
  --local-callback http://127.0.0.1:39155/callback \
  --web-client-id fluxomni-web \
  --web-callback "$MCP_WEB_CALLBACK" \
  --output "$MCP_SETUP_DIR"
```

Copy the web callback from the actual connection management page. The stable ChatGPT callback shown above applies when issuer identification is supported; use the exact URL shown for your connection. Wildcard redirects are rejected.

The private bundle contains:

- `mcp.json`: control-plane configuration, including confidential client secrets.
- `realm.json`: the matching issuer realm and client registrations.
- `issuer-grants.key`: the dedicated issuer-to-control-plane credential.
- `issuer.env`: generated issuer settings and public proxy path matchers. It contains the credential file path, not the credential value.

Mount files individually and read-only. Keep the parent directory private. `realm.json` and the service-key file are readable by the issuer container inside those mounts; opening their parent directory to other host users would expose them. Do not commit the bundle or paste it into a client or model prompt.

The generator creates no human account or password. Provision the issuer account through your normal identity administration process.

Generate the bundle once for a new realm and preserve it. Startup import does not replace an existing realm. Regenerating confidential secrets without updating their issuer registrations will break linking and introspection.

## Configure Compose and HTTPS

Add an operator-owned Compose override to your existing installation. It enables the control-plane resource and forwards its exact paths through the frontend:

```yaml
services:
  control-plane:
    environment:
      FLUXOMNI_MCP_CONFIG: /run/fluxomni-mcp/mcp.json
    volumes:
      - type: bind
        source: ${MCP_SETUP_DIR}/mcp.json
        target: /run/fluxomni-mcp/mcp.json
        read_only: true
        bind:
          create_host_path: false

  frontend:
    environment:
      FLUXOMNI_MCP_PROXY_PATHS: ${MCP_PROXY_PATHS:?Copy the generated literal path matchers}

  mcp-issuer:
    image: fluxomni-mcp-issuer:reviewed
    command: [start, --import-realm]
    restart: unless-stopped
    env_file:
      - ${MCP_SETUP_DIR}/issuer.env
      - ${MCP_SETUP_DIR}/issuer-db.env
    environment:
      KC_HTTP_ENABLED: "false"
      KC_HTTPS_CERTIFICATE_FILE: /run/secrets/issuer.crt
      KC_HTTPS_CERTIFICATE_KEY_FILE: /run/secrets/issuer.key
    ports:
      - "127.0.0.1:9443:8443"
    volumes:
      - type: bind
        source: ${MCP_SETUP_DIR}/realm.json
        target: /opt/keycloak/data/import/realm.json
        read_only: true
        bind:
          create_host_path: false
      - type: bind
        source: ${MCP_SETUP_DIR}/issuer-grants.key
        target: /run/secrets/fluxomni-grants.key
        read_only: true
        bind:
          create_host_path: false
      - type: bind
        source: ${MCP_SETUP_DIR}/issuer.crt
        target: /run/secrets/issuer.crt
        read_only: true
        bind:
          create_host_path: false
      - type: bind
        source: ${MCP_SETUP_DIR}/issuer.key
        target: /run/secrets/issuer.key
        read_only: true
        bind:
          create_host_path: false
```

Create private `issuer-db.env` with `KC_DB=postgres`, `KC_DB_URL`, `KC_DB_USERNAME` and `KC_DB_PASSWORD` for your issuer database. Keep it mode `0600`. Copy the issuer certificate chain and key into the private bundle and allow the issuer container to read those individual files. Do not change the permissions of your original TLS key store.

For a fresh issuer, include `KC_BOOTSTRAP_ADMIN_USERNAME` and a strong `KC_BOOTSTRAP_ADMIN_PASSWORD` in that private environment file for first startup. Create a permanent administrator and the user account in the imported realm, then remove the bootstrap credentials from the file. Issuer roles do not grant Fluxomni permissions.

Copy the generated `FLUXOMNI_MCP_PROXY_PATHS` value into `MCP_PROXY_PATHS` in the environment used to render your override. It contains two literal matchers, for example `/mcp /mcp/*`. Set `MCP_SETUP_DIR` there too. Render the full Compose configuration before applying it. Preserve any installer-managed Compose includes and existing operator overrides.

Serve the issuer's loopback HTTPS listener at its configured public issuer origin through your existing gateway. Preserve the certificate hostname and normal TLS verification. The control plane must reach the issuer, and the issuer must reach the protected grant-service URL. The issuer must be ready before starting the configured control plane; unavailable discovery fails startup closed.

For a private issuer CA, add `issuer_ca_file` to `mcp.json` with its path inside the control-plane container and mount that PEM CA file read-only. For a private control-plane CA, configure the issuer's trusted CA paths. A different backchannel URL can be selected with `--grant-service-url` when generating the bundle; use a fixed HTTPS endpoint reachable from the issuer. Never disable certificate or hostname verification.

The public metadata URL for `/mcp` is `/.well-known/oauth-protected-resource/mcp`. It must return JSON with the exact configured resource and issuer. An unauthenticated request to the resource must return `401` with a Bearer challenge. HTML here means the MCP path reached a frontend fallback: check both the frontend and any outer proxy matchers.

## Link and approve the local account

Sign in to Fluxomni with your named local user, then open **MCP** in the sidebar.

1. Select **Link account** and complete the issuer login.
2. Return to Fluxomni and select the client you want to approve.
3. Select specific visible routes, or explicitly choose all routes you can view.
4. Select **Approve read access**.
5. Start OAuth login from that client using the displayed server address.

Issuer login proves the subject. The local approval separately chooses the client and routes. The client's permissions are always limited by your current Fluxomni role, including when your local role is Admin.

## Connect Codex CLI

Codex CLI 0.162.0 requires the `mcp_2026_07_28` feature. Merge this configuration into your existing Codex configuration; keep any existing feature settings:

```toml
[features]
mcp_2026_07_28 = true

[mcp_servers.fluxomni]
url = "https://stream.example.com/mcp"

[mcp_servers.fluxomni.oauth]
client_id = "fluxomni-codex"
callback_url = "http://127.0.0.1:39155/callback"
callback_port = 39155
```

Then log in using your approved scope:

```bash
codex mcp login fluxomni --scopes "$MCP_SCOPE"
```

Let resource metadata supply the OAuth resource. With this client version, adding an explicit `--oauth-resource` alongside automatic discovery duplicates the authorization parameter and is correctly rejected.

For a private CA, set `CODEX_CA_CERTIFICATE` to its PEM bundle for the client command. Keep normal verification enabled. Use `codex mcp login fluxomni --no-browser` if you need to complete the callback manually.

Ask Codex for your current user, visible routes and playlist readiness for one listed route. Confirm the result includes current `evaluatedAt`, `validUntil`, `readyToAttempt` and findings. Missing media or node facts must remain blocked or unknown. A successful check permits an attempt; it does not prove playback.

## Web chat and lifecycle checks

The web client needs public HTTPS resource and issuer endpoints, a registered client with its actual callback, and support for MCP 2026-07-28. Complete its own OAuth connection and all three tool calls before treating it as supported. A scripted exchange using the web client ID does not prove a real web-chat connection.

Use **Revoke** in Fluxomni to remove one client's local approval. Other clients remain independent. Approving it again creates a new generation; old access and refresh credentials stay denied. Sign in again from the client for a new credential.

Password resets, role changes and user deletion invalidate existing local delegations. Browser sign-out removes the browser session; it does not revoke an independent client approval. Signing-key caching does not cache permission. Issuer or local-store failure denies protected output.

Back up the control-plane SQLite database and issuer PostgreSQL database together with their private deployment configuration. Restoring or rotating issuer secrets is an operator maintenance action; restarting must never recreate a missing approval.
