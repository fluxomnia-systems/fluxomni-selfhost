# Connect a self-hosted Fluxomni Installation

Use this guide to enroll a public HTTPS Installation and approve read access for an AI agent. A named local Admin must complete ownership registration.

Start with the distributed Compose installation. Confirm the control plane is healthy and that a named local Admin can sign in. A password-only Installation can use Connect. Local OIDC remains an independent option.

The standard single-server installer configures private RPC automatically. Its `control-init` service creates the internal TLS certificate, private key and local media-node credential in persistent Docker volumes. The media node uses those files to connect to `https://control-plane:50052`. Keep the volumes when restarting or updating. Confirm that the media node logs `Registered media node with control plane`.

If you use custom Compose files, confirm they already provide authenticated private RPC before proceeding. Keep the RPC port private. The frontend needs its own HTTPS configuration for browser and Connect traffic.

Give the frontend a public HTTPS origin with a trusted certificate. Route the Installation's browser and gateway HTTP requests to the frontend. Configure the same canonical HTTPS origin in the gateway JSON and in FLUXOMNI_PUBLIC_URL. Use the origin without a trailing slash in the JSON.

## Standard installer

To enable Connect during a fresh standard install, set `FLUXOMNI_PUBLIC_URL`, `FLUXOMNI_CONNECT_GATEWAY_KEY_ID` and `FLUXOMNI_CONNECT_GATEWAY_PUBLIC_KEY` in the installer environment. The installer creates the gateway configuration and checks the combined Compose files before starting services. Existing installations must use drained maintenance when enabling Connect.

After setup, proceed to [Register the Installation](#register-the-installation).

## Custom Compose setup

Create `gateway.json` with the canonical HTTPS origin, a UUID v4 and your Connect environment's verification key. Encode the 32 raw Ed25519 public-key bytes as unpadded base64url.

```json
{
  "origin": "https://installation.example",
  "installationId": "11111111-1111-4111-8111-111111111111",
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

In Settings → Connected Apps, start registration and copy the registration details. Sign in to Fluxomni Connect and submit them in Installations. Return to the local screen to review and confirm the account. Submit the same registration again. The portal reports Installation registered when the registry activates it.

Use an AI agent that supports remote MCP over HTTPS with OAuth. Add the MCP URL supplied for your Connect environment and sign in using the agent’s setup flow. For example, in Codex CLI:

```sh
codex mcp add fluxomni --url https://connect.example/mcp
codex mcp login fluxomni
```

Replace the example URL with your environment's MCP endpoint. In a conversation with your AI agent, ask it to call `fluxomni_begin_link`. Paste the handoff token and the local linking details into the portal, then prepare the request. Review and approve read access locally. Submit the signed receipt in the portal and ask the same AI agent connection to call `fluxomni_complete_link` with the displayed generation. Repeat the approval for each agent connection.

To remove access, revoke the specific approval locally and submit the revocation notification. Verify that a new read is denied. If the Installation ownership key is lost, register with a new Installation ID and approve each client again.

## Troubleshooting

- If Connected Apps is unavailable, confirm the control plane loaded the mounted gateway configuration, then sign in as a named local Admin.
- If starting registration fails after sign-in, check that the control-plane process owns its data directory and that the gateway key directory has mode 0700. This can fail when a host user creates a bind mount and the container runs under a different UID.
- If registration cannot verify the Installation, check that the public HTTPS origin is reachable, matches the JSON exactly and serves the gateway ownership endpoint without a redirect or browser challenge.
- Keep the local browser session that started registration until you finish local confirmation. If the portal response is lost, submit the same registration again with the same Connect account. When the portal has already retained a signed callback, it reserves that registration for exact retry until 24 hours after the challenge expires. A fresh registration for that Installation or origin may be rejected during this window. If you can no longer confirm the original registration, wait for the reservation to expire before creating a replacement.
- If an AI agent can sign in but cannot inspect an Installation, check that the same agent connection completed the link and that its local approval is active. Review the local role and route scope before changing the approval.

## Clean-install evidence

Record the release, image digest, origin, cloud revision, and client version. Start with a password-only Installation. If you use local OIDC, repeat the checks with your configured issuer. Confirm the approved route is visible, a route outside the local approval is denied, and media already running continues during a gateway outage.
