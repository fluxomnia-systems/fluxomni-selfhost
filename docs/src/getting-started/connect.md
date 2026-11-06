# Connect a self-hosted Fluxomni Installation

Use this guide to enroll a public HTTPS Installation and approve read access for an AI agent. A named local Admin must complete ownership registration.

Connect is optional. An AI agent can also use [native MCP](../api/mcp.md) directly, with its separate local OAuth setup. Connect provides a shared cloud MCP endpoint and does not replace local permissions.

This guide describes guided setup. Use matching control-plane and frontend builds that include this workflow; stable 26.3.2 alone is not its acceptance evidence. Use the reviewed image versions supplied for your environment.

Start with the distributed Compose installation. Confirm the control plane is healthy and that a named local Admin can sign in. A password-only Installation can use Connect. Local OIDC remains an independent option.

The standard single-server installer configures private RPC automatically. Its `control-init` service creates the internal TLS certificate, private key and local media-node credential in persistent Docker volumes. The media node uses those files to connect to `https://control-plane:50052`. Keep the volumes when restarting or updating. Confirm that the media node logs `Registered media node with control plane`.

If you use custom Compose files, confirm they already provide authenticated private RPC before proceeding. Keep the RPC port private. The frontend needs its own HTTPS configuration for browser and Connect traffic.

Give the frontend a public HTTPS origin with a trusted certificate. Route the Installation's browser and gateway HTTP requests to the frontend. Configure the same canonical HTTPS origin in the gateway JSON and in FLUXOMNI_PUBLIC_URL. Use the origin without a trailing slash in the JSON.

## Builds and client versions

Use the image versions qualified for your Connect environment and record their resolved digests. Moving `edge` or `latest` tags and the application's version label alone do not identify the tested build. Keep the saved Installation ID, keys, data and private RPC volumes during upgrades; follow [Drained maintenance](capacity-upgrades.md).

Standards-compatible AI agents use their own remote MCP and OAuth settings. Record the actual agent version when checking its discovery, login, linking and read workflows. Native MCP remains a separate direct connection option.

## Standard installer

To enable Connect during a fresh standard install, set `FLUXOMNI_PUBLIC_URL`, `FLUXOMNI_CONNECT_GATEWAY_KEY_ID` and `FLUXOMNI_CONNECT_GATEWAY_PUBLIC_KEY` in the installer environment. The portal defaults to `https://connect.fluxomni.io`. The installer creates the gateway configuration and checks the combined Compose files before starting services. Existing installations must use drained maintenance when enabling Connect.

Connect origin validation requires Python 3 on the host. Run the normal Bash/Docker installer; no separate Python installer command is needed.

The public verification key comes from the operator of your Connect environment. It is public configuration, not a secret to generate yourself. The installer creates and retains the Installation ID; the Installation creates its own private ownership key. Do not put OAuth client secrets or AI-agent tokens into these fields.

For staging or another Connect operator, set the advanced `FLUXOMNI_CONNECT_PORTAL_ORIGIN` override to its HTTPS origin without a trailing slash, for example `https://connect.example`. It must differ from the Installation origin. On an existing installer-managed installation, explicitly supplying it adds or updates only browser navigation; omitting it preserves the saved configuration, including older files without a portal address. It never replaces the Installation ID or gateway verification key. Keep existing keys and state on upgrades.

After setup, proceed to [Register the Installation](#register-the-installation).

## Custom Compose setup

Create `gateway.json` with the canonical HTTPS origin, a UUID v4 and your Connect environment's verification key. Encode the 32 raw Ed25519 public-key bytes as unpadded base64url.

```json
{
  "origin": "https://installation.example",
  "installationId": "11111111-1111-4111-8111-111111111111",
  "portalOrigin": "https://connect.example",
  "initialGatewayKey": {
    "keyId": "REPLACE_WITH_GATEWAY_KEY_ID",
    "publicKey": "REPLACE_WITH_GATEWAY_PUBLIC_KEY"
  }
}
```

Keep the Installation ID on reruns. The Installation generates its own ownership key.

Add a Compose override such as docker-compose.connect.yml:

```yaml
services:
  frontend:
    environment:
      FLUXOMNI_MCP_PROXY_PATHS: /mcp-gateway/*
  control-plane:
    environment:
      FLUXOMNI_MCP_GATEWAY_CONFIG: /run/fluxomni/gateway.json
    volumes:
      - ./gateway.json:/run/fluxomni/gateway.json:ro
```

Set `FLUXOMNI_PUBLIC_URL` in `.env` to the same origin as `gateway.json`. If you already proxy a native MCP path, retain its existing literal matchers and add `/mcp-gateway/*` to the same space-separated value.

For a fresh installation with no active or previously reserved routes, validate the Compose files and start the stack:

```sh
docker compose -f docker-compose.yml -f docker-compose.connect.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.connect.yml up -d
```

For an existing installation, follow [Drained maintenance](capacity-upgrades.md) before applying these overrides. Disable affected routes and wait for reservations to reach zero. Apply the Compose changes during the drained maintenance window and follow the guide to restore routes.

Include any existing site override files in both commands. Pin the image version during verification and record the resolved image digests.

## Register the Installation

1. Sign in as a named local Admin and open **Settings → Connected apps**.
2. Select **Start registration**. The browser opens the configured Connect portal; no registration JSON needs copying.
3. Sign in through your invited Connect email account and select **Continue registration**.
4. Back on the Installation, review the exact Connect account and select **Confirm Connect account**.
5. The browser returns to Connect and completes the signed acknowledgment. Wait for **Installation registered**.

Keep the same local browser session until confirmation. Registration establishes the owner only; it does not approve any AI client, even for an Admin.

## Connect an AI agent

Use any AI agent that supports remote MCP over HTTPS with OAuth. Add the MCP endpoint supplied for your Connect environment and complete the agent's sign-in flow. Codex CLI is one example:

```sh
codex mcp add fluxomni --url https://connect.example/mcp
codex mcp login fluxomni
```

Other agents use their own MCP settings. These commands are not required when your agent provides a settings screen. A successful OAuth login alone does not grant Installation access.

1. Ask the agent to connect to your Installation. It calls `fluxomni_begin_link` and gives you a verification link.
2. Open that link, sign in with the same Connect account and select the registered Installation. A personal account can also enter an already registered public HTTPS origin.
3. On the Installation, sign in as your named local user. Review the global account and AI client, then select **Approve read access**.
4. The signed receipt returns automatically to Connect. Return to the original agent conversation and ask it to finish connecting. That same OAuth connection calls `fluxomni_complete_link` with its original request ID.
5. Confirm that the portal reports **Connected**, then ask the agent to list visible routes or check readiness for one listed route.

Approve each AI client separately. Current local roles, route limits and account security still apply. A readiness result permits an attempt; it does not prove playback or destination acceptance.

## Revoke access and recover failures

In the Installation's **Connected apps**, select **Revoke local access** for the specific approval. Local denial commits first; the browser then notifies Connect automatically. If delivery fails, retry the same revocation notification. A notification failure does not restore local access. Verify a new read from that agent is denied.

Signing out of the portal removes that browser session; it does not revoke independent AI-client approvals. To retire the whole cloud registration, open its owner view and select **Retire registration**, review the exact origin and ID, then confirm. This ends Connect access for all clients on that registration. Reconnecting requires a new Installation ID and fresh approvals.

If the Installation key is lost, use named-Admin recovery with an exact transaction ID, old Installation ID and fresh replacement ID. Install the public replacement configuration returned by the recovery service and restart the matched control plane. Retire the old cloud registration and Egress target through their supported owners, then register the replacement and approve each client again. Preserve trust, replay and revoked history. Do not reset databases, edit authority SQL, restore a pre-revocation backup or recreate the lost key.

## Troubleshooting

- If Connected Apps is unavailable, confirm the control plane loaded the mounted gateway configuration, then sign in as a named local Admin.
- If starting registration fails after sign-in, check that the control-plane process owns its data directory and that the gateway key directory has mode 0700. This can fail when a host user creates a bind mount and the container runs under a different UID.
- If registration cannot verify the Installation, check that the public HTTPS origin is reachable, matches the JSON exactly and serves the gateway ownership endpoint without a redirect or browser challenge.
- If the page says Direct MCP is not configured, this describes the separate local OAuth endpoint. Check the Connect registration and personal approval below it.
- If Start registration is disabled, check the configured Connect portal origin and use matching guided-setup images.
- Keep the local browser session that started registration until you finish local confirmation. If the portal response is lost, use Continue in Connect or the explicit retry for the same transaction and Connect account. When the portal has already retained a signed callback, it reserves that registration for exact retry until 24 hours after the challenge expires. A fresh registration for that Installation or origin may be rejected during this window. If the local session changes or a pending action expires, start a new local transaction; do not extend or adopt the old session binding. A new portal login for the same global account is separate from the initiating local session.
- If a pending link expires, start a new request in the same AI agent. If local approval already committed, retry that original request to recover its receipt; do not create another approval just because a response was lost.
- If an AI agent can sign in but cannot inspect an Installation, check that the same agent connection completed the link and that its local approval is active. Review the local role and route scope before changing the approval.

## Clean-install evidence

Record the release, image digest, origin, cloud revision, and client version. Start with a password-only Installation. If you use local OIDC, repeat the checks with your configured issuer. Confirm the approved route is visible, a route outside the local approval is denied, and media already running continues during a gateway outage.
