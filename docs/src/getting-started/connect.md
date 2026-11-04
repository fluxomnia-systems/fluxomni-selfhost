# Connect a self-hosted Fluxomni Installation

Use this guide to enroll a public HTTPS Installation and approve read access for an AI agent. A named local Admin must complete ownership registration.

Start with the distributed Compose installation. Confirm the control plane is healthy and that a named local Admin can sign in. A password-only Installation can use Connect. Local OIDC remains an independent option.

For an edge build that requires a node credential, assign each media node its own random credential file. Create the credential file from the Compose project directory:

```sh
(
  umask 077
  mkdir -p ./rpc
  set -C
  openssl rand -hex 32 | tr -d '\n' > ./rpc/node-credential
)
```

Put its SHA-256 hex digest in a JSON object keyed by the exact media-node ID. Mount the digest map read-only on the control plane and set `FLUXOMNI_NODE_CREDENTIALS_FILE` to the mounted path. Mount each original credential read-only only on its media node and set `FLUXOMNI_NODE_CREDENTIAL_FILE`.

Set `FLUXOMNI_CONTROL_PLANE_RPC_BIND=0.0.0.0:50052` inside the private Compose network. Keep RPC off public host ports. Mount a server certificate and key through `FLUXOMNI_CONTROL_TLS_CERT` and `FLUXOMNI_CONTROL_TLS_KEY`. The leaf certificate must have `CA:FALSE`, server authentication usage, and a DNS SAN matching the Compose service name `control-plane`. Mount its issuing CA on the media node through `FLUXOMNI_CONTROL_TLS_CA` and set `FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT=https://control-plane:50052`. Confirm that the media node logs `Registered media node with control plane`.

For a single media node, put the files under `./rpc` and save this example as `docker-compose.rpc.yml`. In `credential-hashes.json`, use the same node ID as `FLUXOMNI_MEDIA_NODE_ID` in `.env`. Make the files readable by the process in each container and restrict host access to the private key and node credential.

```yaml
services:
  control-plane:
    ports: !reset []
    environment:
      FLUXOMNI_CONTROL_PLANE_RPC_BIND: 0.0.0.0:50052
      FLUXOMNI_CONTROL_TLS_CERT: /run/fluxomni-rpc/server.crt
      FLUXOMNI_CONTROL_TLS_KEY: /run/fluxomni-rpc/server.key
      FLUXOMNI_NODE_CREDENTIALS_FILE: /run/fluxomni-rpc/credential-hashes.json
    volumes:
      - ./rpc/server.crt:/run/fluxomni-rpc/server.crt:ro
      - ./rpc/server.key:/run/fluxomni-rpc/server.key:ro
      - ./rpc/credential-hashes.json:/run/fluxomni-rpc/credential-hashes.json:ro
  media-node:
    environment:
      FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT: https://control-plane:50052
      FLUXOMNI_CONTROL_TLS_CA: /run/fluxomni-rpc/ca.crt
      FLUXOMNI_NODE_CREDENTIAL_FILE: /run/fluxomni-rpc/node-credential
    volumes:
      - ./rpc/ca.crt:/run/fluxomni-rpc/ca.crt:ro
      - ./rpc/node-credential:/run/fluxomni-rpc/node-credential:ro
```

The override removes the host port mapping for the control plane. The media node still connects over the private Compose network. Include `-f docker-compose.rpc.yml` after the base Compose file when running the commands below.

Give the frontend a public HTTPS origin with a trusted certificate. Route the Installation's browser and gateway HTTP requests to the frontend. Configure the same canonical HTTPS origin in the gateway JSON and in FLUXOMNI_PUBLIC_URL. Use the origin without a trailing slash in the JSON.

Generate a UUID v4 for installationId and obtain the verification key and key ID for your Connect environment. Save them in gateway.json. Use the unpadded base64url encoding of 32 raw Ed25519 public-key bytes for initialGatewayKey.publicKey. The gateway public key verifies incoming signatures. The Installation generates its own ownership key.

Use this shape for gateway.json. Replace the example origin, Installation ID, key ID and public key with values for the target environment.

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

Validate the Compose files and apply them to the frontend and control plane:

```sh
docker compose -f docker-compose.yml -f docker-compose.connect.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.connect.yml up -d
```

Include any existing site override files in both commands. Pin the image version during verification and record the resolved image digests.

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
