# Native MCP access

Use native MCP to inspect the instance and optionally manage routes, library files, playlists and outputs. Each client needs a local approval, and every request remains limited by your current account permissions.

This is a preview integration. It requires a Fluxomni build containing [the native MCP runtime](https://github.com/fluxomnia-systems/fluxomni/pull/437), including its matching frontend and the [unified sign-in implementation](https://github.com/fluxomnia-systems/fluxomni/issues/439). Stable 26.3.2 alone does not provide this feature. The isolated issuer and Codex CLI workflow are verified; an actual web-chat connection remains an acceptance gate.

## Prepare the instance

Use the same public HTTPS origin for the operator UI and MCP resource, for example `https://stream.example.com/mcp`. Run a separate HTTPS issuer, for example `https://auth.example.com/realms/fluxomni`.

You need:

- A reviewed Fluxomni source checkout matching the deployed control plane and frontend.
- PostgreSQL and the normal production TLS configuration for the separate issuer.
- A local named Fluxomni user bound to a verified issuer account. New instances use the host setup below.
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
  --browser-client-id fluxomni-browser \
  --issuer-label "Fluxomni accounts" \
  --web-client-id fluxomni-web \
  --web-callback "$MCP_WEB_CALLBACK" \
  --output "$MCP_SETUP_DIR"
```

Copy the web callback from the actual connection management page. The stable ChatGPT callback shown above applies when issuer identification is supported; use the exact URL shown for your connection. Wildcard redirects are rejected.

The private bundle contains:

- `mcp.json`: MCP resource configuration and its confidential introspection credential.
- `oidc.json`: browser sign-in configuration, trusted issuer label and separate confidential browser client credential.
- `realm.json`: the matching issuer realm and client registrations.
- `issuer-grants.key`: the dedicated issuer-to-control-plane credential.
- `issuer.env`: generated issuer settings and public proxy path matchers. It contains the credential file path, not the credential value.

Mount files individually and read-only. Keep the parent directory private. `realm.json` and the service-key file are readable by the issuer container inside those mounts; opening their parent directory to other host users would expose them. Do not commit the bundle or paste it into a client or model prompt.

The generator creates no human account or password. Provision the issuer account through your normal identity administration process.

Generate the bundle once for a new realm and preserve it. Startup import does not replace an existing realm. Regenerating confidential secrets without updating their issuer registrations will break browser sign-in and introspection.

## Configure Compose and HTTPS

Add an operator-owned Compose override to your existing installation. It enables the control-plane resource and forwards its exact paths through the frontend:

```yaml
services:
  control-plane:
    environment:
      FLUXOMNI_MCP_CONFIG: /run/fluxomni-mcp/mcp.json
      FLUXOMNI_OIDC_CONFIG: /run/fluxomni-mcp/oidc.json
    volumes:
      - type: bind
        source: ${MCP_SETUP_DIR}/mcp.json
        target: /run/fluxomni-mcp/mcp.json
        read_only: true
        bind:
          create_host_path: false
      - type: bind
        source: ${MCP_SETUP_DIR}/oidc.json
        target: /run/fluxomni-mcp/oidc.json
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

The matching frontend build already forwards `/.well-known/oauth-protected-resource*` to the control plane, separately from those generated resource matchers. Any outer or custom proxy must also forward `/mcp`, `/mcp/*`, `/.well-known/oauth-protected-resource` and `/.well-known/oauth-protected-resource/mcp` to that frontend or directly to the control plane. Replace `/mcp` with your chosen resource path. Check the public metadata URL through every proxy before starting client OAuth.

Serve the issuer's loopback HTTPS listener at its configured public issuer origin through your existing gateway. Preserve the certificate hostname and normal TLS verification. The control plane must reach the issuer, and the issuer must reach the protected grant-service URL. Invalid local configuration stops startup. A temporarily unavailable issuer leaves the control plane and sign-in page running, but new identity verification and protected MCP calls fail closed. Retry after restoring the issuer; no password fallback opens.

For a private issuer CA, add `issuer_ca_file` to `oidc.json` with its path inside the control-plane container and mount that PEM CA file read-only. For a private control-plane CA, configure the issuer's trusted CA paths. A different backchannel URL can be selected with `--grant-service-url` when generating the bundle; use a fixed HTTPS endpoint reachable from the issuer. Never disable certificate or hostname verification.

The public metadata URL for `/mcp` is `/.well-known/oauth-protected-resource/mcp`. It must return JSON with the exact configured resource and issuer. An unauthenticated request to the resource must return `401` with a Bearer challenge. HTML here means the MCP path reached a frontend fallback: check both the frontend and any outer proxy matchers.

## First-user setup

With issuer sign-in configured, an empty user directory does not open an anonymous Admin shell. A host operator creates the first named Admin and a ten-minute, single-use enrollment token while the control plane is stopped.

Use the matched control-plane image and the same mounted data directory as your installation:

```bash
docker compose stop control-plane
docker compose run --rm --no-deps \
  --volume "$MCP_SETUP_DIR:/run/fluxomni-setup" \
  control-plane \
  auth bootstrap-admin \
  --username admin \
  --token-file /run/fluxomni-setup/enrollment.token
docker compose up -d control-plane
```

The command refuses a running database owner or an existing user directory. It creates the token file with owner-only permissions and never overwrites it. A failed token write or sync rolls back the account change.

Open Fluxomni, select **Set up an existing account**, and enable **Use a host-issued setup token**. Enter the local username and token from the private file. Continue to the issuer, then confirm the displayed local account and verified issuer identity. The host token cannot access GraphQL or MCP and is consumed when setup starts. If that flow expires or the server restarts, use administrator recovery to issue a fresh token.

The generator does not create an issuer account. Provision that account through your identity administration process before completing enrollment. Issuer roles and matching email addresses never create a local Admin.

## Enroll an existing local account

Existing verified issuer bindings are preserved. Their users can select **Continue with** the configured issuer immediately, using their existing issuer session where possible.

An unbound local user selects **Set up an existing account**, proves their local username and password, and completes issuer verification. That local password only starts restricted setup; it does not open the application. Confirm both displayed identities before the binding is saved. Select **Use a different issuer account** if the wrong issuer session is open.

With OIDC configured, local passwords no longer create normal browser sessions. A local password cannot replace an existing binding. Admins still create local users and assign local roles under **Settings → Users**; the initial local password is only setup proof for an unbound user.

Browser OIDC can run without MCP by loading only `oidc.json`. MCP requires browser OIDC for the exact same issuer and public origin. The MCP resource, browser client and introspection client keep separate credentials and audiences.

## Sign in and approve a client

Select **Continue with** the configured issuer to sign in to Fluxomni, then open **Settings → Connected apps**. A valid issuer browser session can satisfy this redirect without another password entry. The callback returns to the original application page.

1. Select **Approve a client** and choose the registered client.
2. Select specific visible routes, or explicitly choose all routes you can view.
3. Select **Approve read access**.
4. Start OAuth login from that client using the displayed server address and the same issuer account.

Connected apps uses the identity verified by your browser sign-in. No normal **Link account** step remains. Sign-in does not approve a client. Your current local role and route ownership limit every client request, including requests from Admin users.

## Administrator recovery

Restore issuer availability before completing recovery. Existing unexpired local sessions retain their configured lifetime and local revision checks during an issuer outage; the outage does not renew them. No public password fallback is enabled.

For a lost Admin identity, stop the control plane and take a consistent backup of its data and private configuration. Run the matched image against that same data directory:

```bash
docker compose stop control-plane
docker compose run --rm --no-deps \
  --volume "$MCP_SETUP_DIR:/run/fluxomni-setup" \
  control-plane \
  auth recover-admin \
  --username admin \
  --issuer "$MCP_ISSUER" \
  --remove-subject exact-subject-being-repaired \
  --token-file /run/fluxomni-setup/recovery.token
docker compose up -d control-plane
```

The command displays the target local account and selected subject. Repeat `--remove-subject` only for verified bindings being repaired; omit it when issuing a fresh setup token without removing a binding. Recovery keeps the local role, rotates its security revision and invalidates its old sessions and delegated grants. Removed identities' approvals are retired in the same transaction. Another user's bindings stay unchanged.

Enter the recovery token through **Set up an existing account**, verify the restored issuer identity, and confirm it. Old access and refresh credentials stay denied after recovery, binding recreation and reapproval. A failed token write, sync or database commit does not claim recovery success.

This command targets existing local Admins. For an Operator or Viewer, recover the existing issuer account and stable subject through issuer administration; replacing their issuer subject is outside this Admin recovery command.

## Cut over an existing deployment

Schedule a maintenance window and stop authentication changes. Preserve a consistent SQLite data-directory backup and the matching private bundle, issuer database backup and application image refs before changing the schema or clients.

Preserve the existing `issuer`, `resource`, `scope`, tool names, public client IDs, `introspection_secret` and `issuer_service_key` in `mcp.json`. Do not rerun the new-realm generator over an existing installation: it generates new secrets.

Register a new confidential browser client in the existing issuer with standard code flow and S256. Put its actual registered client ID and secret in a new `oidc.json` as `client_id` and `client_secret`. Set `issuer` to the same issuer as `mcp.json`, `origin` to the application HTTPS origin without a trailing slash, and `issuer_label` to your chosen display label. Move any private `issuer_ca_file` setting from `mcp.json` to `oidc.json`; its path must exist inside the control-plane container.

Remove `link_client_id` and `link_client_secret` from `mcp.json`. These old fields are not accepted by the new binary. The original issuer/subject bindings stay intact because they belong to local users, independently of the browser client ID. Retire the old account-link client after verifying the new sign-in flow; do not replace the public MCP clients or their introspection registration.

Update the separate confidential browser client's exact callback to `/api/auth/oidc/callback` on the configured application origin, and register that origin's `/?auth=signed-out` as its post-logout redirect. Existing realm import does not update client registrations: use issuer administration for an existing realm. Keep local/public MCP clients and the resource introspection client separate.

Deploy the matched control-plane/frontend build and the new `mcp.json` plus `oidc.json` mounts together. Remove the old account-link fields and callback registration; no compatibility alias is retained. All browsers sign in again. Verify first-user or existing-user enrollment, return paths, client/route approval and revoke/reapproval before reopening access.

Rollback uses the prior matched images, configuration and pre-cutover database snapshot together. Do not run an old binary against the upgraded schema. If credentials were issued or revoked after the snapshot, invalidate affected issuer sessions and recovered account authority before reopening access; a restored backup may contain earlier approvals. Prefer forward recovery once security state has changed.

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

## Enable management access

Management requires a build containing [the MCP management implementation](https://github.com/fluxomnia-systems/fluxomni/issues/440). Deploy the matching frontend and control plane. It is disabled unless private MCP settings name a separate management scope.

For a new realm, add `--management-scope your-approved-management-scope` to the generator command above. Keep it distinct from the inspection scope. The generator registers both as optional scopes for each public client and writes `management_scope` into `mcp.json`. The ten management tool names below are reserved; do not use them as the three configurable inspection names.

For an existing realm, do not regenerate its secrets. Add the separate optional client scope through issuer administration and assign it to both registered public clients. Add the same exact value as `management_scope` in the existing private `mcp.json`, preserve the other settings, and restart the control plane. Removing this setting disables the management catalog.

In **Settings → Connected apps**, select the client and routes, then enable **Allow management of routes, playlists and outputs**. Review the permissions and approve. Management is off by default. Approval is once per client; permitted changes do not require returning to this page each time.

Set `MCP_MANAGEMENT_SCOPE` to the exact registered value and sign in again requesting both scopes:

```bash
codex mcp login fluxomni --scopes "$MCP_SCOPE,$MCP_MANAGEMENT_SCOPE"
```

Your MCP client can also require its own tool approvals. Those are separate from Fluxomni permissions. If you trust this specific server and want to approve its tools once, Codex 0.162.0 supports this server-scoped setting in the existing configuration:

```toml
[mcp_servers.fluxomni]
url = "https://stream.example.com/mcp"
scopes = ["your-approved-inspection-scope", "your-approved-management-scope"]
default_tools_approval_mode = "approve"
```

Use your actual scope values. This only changes Codex prompts for that server; it does not bypass Fluxomni's current role, scope, approval or route checks. You can keep prompting or set individual tool approval rules instead. See the [official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

Also include both scopes in the client's saved `scopes` list. Approving management locally does not add a scope to an existing token. Existing read approvals remain read-only, and approving again does not revive earlier credentials.

### Management tools

The catalog contains typed tools around the normal application services:

- `fluxomni_route` inspects a route, its sources and paginated outputs.
- `fluxomni_save_route` creates or updates a route; `fluxomni_route_action` enables, disables or deletes it.
- `fluxomni_files` lists or inspects library processing state. `fluxomni_import_file` queues a Google Drive file ID through the configured integration. It does not upload local files or fetch arbitrary URLs.
- `fluxomni_delete_files` deletes unused library files using existing reference safeguards. It never forces removal from playlists or saved programs.
- `fluxomni_playlist` reads ordered placements and the queue revision. `fluxomni_set_playlist` replaces the complete ordered queue to add, remove or reorder files.
- `fluxomni_save_output` adds or edits an output; `fluxomni_output_action` enables, disables or deletes it.

Tools return identifiers and bounded state without stored source/destination credentials, private paths or raw processing errors. A queued import is not a completed download. Saved configuration is not evidence of playback or destination acceptance.

### Permission limits

A selected-route approval can manage only those existing routes and their playlists and outputs. Creating routes and changing the shared library require an **all routes** management approval. Normal role and ownership rules still apply: Operators create routes they own, Viewers cannot manage configuration, and only Admins can delete library files. File-backed sources and playlists also obey library visibility rules.

Revoke the approval to prevent further admission. Queued route writes recheck authority after their owning lock wait. An accepted library cleanup or import may finish after revocation. Revocation does not undo completed changes.

### Readback and retries

Read the complete playlist, including every page, before replacing it. Supply its current `expectedQueueRevision` and preserve placement IDs for existing entries. On a revision conflict, reload before saving. Existing entries whose catalog row is missing can still be removed or reordered; new missing media and hidden files are rejected.

Route edits preserve omitted sources and node pin. Send `"pinnedMediaNodeId": null` to clear an existing pin and restore automatic placement. Output edits preserve an omitted destination plus existing audio and mixins. Omitted labels clear the label. Source IDs retain unchanged credentials; omitted pull URLs and SRT passphrases retain their existing values. Pull sources require RTMP(S) or HTTP(S) network URLs; use managed file IDs for file sources.

Creates are not automatically retryable. After a timeout, disconnect or uncertain response, inspect the current routes, outputs, files or playlist before retrying. A response withheld after revocation does not prove an earlier admitted change failed. There is no separate preview, plan or apply tool.

## Web chat and lifecycle checks

The web client needs public HTTPS resource and issuer endpoints, a registered client with its actual callback, and support for MCP 2026-07-28. Complete its own OAuth connection and all three tool calls before treating it as supported. A scripted exchange using the web client ID does not prove a real web-chat connection.

Use **Revoke** in Fluxomni to remove one client's local approval. Other clients remain independent. Approving it again creates a new generation; old access and refresh credentials stay denied. Sign in again from the client for a new credential.

Local role/security changes and user deletion invalidate existing local delegations. **Sign out of Fluxomni** removes the selected local browser session and pending sign-in/setup actions; it keeps issuer SSO and independent client approvals. A later sign-in requires an explicit click.

**Sign out of identity provider** first signs out locally, then redirects to the configured issuer's logout endpoint. If the issuer is unavailable, local sign-out still succeeds and Fluxomni reports that issuer sign-out was not confirmed. Provider logout can invalidate MCP credentials through issuer activity checks, but does not rewrite local approval history. It does not promise logout from other applications or browsers. Signing-key caching does not cache permission. Issuer or local-store failure denies protected output.

Back up the control-plane SQLite database and issuer PostgreSQL database together with their private deployment configuration. Restoring or rotating issuer secrets is an operator maintenance action; restarting must never recreate a missing approval.
