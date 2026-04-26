# Private Access & Tunnels

Run FluxOmni on a private overlay network when the Control Surface and media ports should be reachable only from your own devices or servers.

This page shows Tailscale first because it is the easiest private-network option for most self-host deployments. The same FluxOmni rule applies to every option: set the advertised hosts to the address that your publishers, viewers, and extra media nodes can actually reach.

## When to Use This

Use private access when you want a home lab, creator workstation, staging server, or internal fleet that is not exposed directly to the public internet.

Private overlays are a good fit for:

- operator access to `/routes`, `/fleet`, and settings
- private RTMP/SRT publish tests from your own machines
- remote media nodes that register over a private control path
- staging deployments before opening public media ports

They are not a replacement for a public ingest or viewer edge. If guests, customers, or platforms outside your private network need to publish or watch, use public DNS and firewall rules for those media ports.

## Tailscale Single-Host Install

Add the server as a new device in Tailscale, join your tailnet, then install FluxOmni with the server's Tailscale IP as the advertised host.

1. Open [Tailscale's Add device page](https://login.tailscale.com/admin/machines/new).
2. Choose the server OS and copy the setup command Tailscale gives you.
3. Run that command on the server, then bring the device online with `sudo tailscale up --ssh` if the setup command did not already do that.

After the device appears in your tailnet, run:

```bash
#!/usr/bin/env bash
set -euo pipefail

sudo tailscale up --ssh

TS_IP="$(tailscale ip -4 | head -n1)"
if [ -z "$TS_IP" ]; then
  echo "Could not detect a Tailscale IPv4 address" >&2
  exit 1
fi

# Install FluxOmni so generated UI, RTMP, HLS, and SRT URLs use the tailnet IP.
curl -fsSL https://install.fluxomni.io | \
  FLUXOMNI_PUBLIC_HOST="$TS_IP" \
  FLUXOMNI_MEDIA_NODE_PUBLIC_HOST="$TS_IP" \
  bash

printf '\nFluxOmni Control Surface: http://%s\n' "$TS_IP"
printf 'RTMP/SRT/HLS media ports are reachable from tailnet devices on the same host.\n'
```

From a device in the same tailnet, open:

```text
http://100.x.y.z/routes
```

The default media addresses shown in the route workspace will use the same Tailscale IP:

```text
rtmp://100.x.y.z:1935/live/<publish-key>
srt://100.x.y.z:10080?streamid=...
http://100.x.y.z:8000/...
```

## Tailscale MagicDNS Names

If MagicDNS is enabled in the Tailscale admin console, you can advertise the node name instead of the `100.x.y.z` IP.

```bash
TS_DNS="fluxomni-box.your-tailnet.ts.net"

curl -fsSL https://install.fluxomni.io | \
  FLUXOMNI_PUBLIC_HOST="$TS_DNS" \
  FLUXOMNI_MEDIA_NODE_PUBLIC_HOST="$TS_DNS" \
  bash
```

Use the IP form if Docker containers on the host cannot resolve your MagicDNS name. Generated artifact URLs and media-node callbacks must be reachable from the containers, not only from your laptop.

## Optional Tailscale Serve

Tailscale already encrypts traffic between tailnet devices. Use Tailscale Serve when you want a private `https://...ts.net` URL for the web UI, or when Docker-published ports time out over Tailscale even though Tailscale SSH and `tailscale ping` work.

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${TS_DNS:?Set TS_DNS to your MagicDNS name, for example fluxomni-box.your-tailnet.ts.net}"

# First add this host from https://login.tailscale.com/admin/machines/new,
# then make sure it is online in your tailnet.
sudo tailscale up --ssh

# Bind the FluxOmni HTTP container port to localhost, then let Tailscale Serve
# publish it privately on https://$TS_DNS.
curl -fsSL https://install.fluxomni.io | \
  FLUXOMNI_CONTROL_PLANE_HTTP_PORT=127.0.0.1:8080 \
  FLUXOMNI_PUBLIC_HOST="$TS_DNS" \
  FLUXOMNI_PUBLIC_URL="https://$TS_DNS" \
  FLUXOMNI_MEDIA_NODE_PUBLIC_HOST="$(tailscale ip -4 | head -n1)" \
  bash

sudo tailscale serve --bg --https=443 http://127.0.0.1:8080

printf '\nFluxOmni Control Surface: https://%s\n' "$TS_DNS"
```

Tailscale Serve can also forward the plain HTTP UI and TCP media ports when direct Docker-published ports are not reachable over the tailnet:

```bash
# UI over plain HTTP, useful when http://<tailnet-name>/routes times out.
sudo tailscale serve --bg --http=80 http://127.0.0.1:80

# RTMP and HLS/WebRTC TCP over the tailnet.
sudo tailscale serve --bg --tcp=1935 tcp://127.0.0.1:1935
sudo tailscale serve --bg --tcp=8000 tcp://127.0.0.1:8000

# Control-plane gRPC for standalone media-node registration.
sudo tailscale serve --bg --tcp=50052 tcp://127.0.0.1:50052

# Inspect or reset the current Serve config.
tailscale serve status
# sudo tailscale serve reset
```

This is a Tailscale/Docker forwarding workaround, not a FluxOmni setting. Tailscale Serve does not forward SRT UDP (`10080/udp`), so use RTMP for private tailnet ingest/testing when you rely on Serve forwarding.

If you use a Tailscale Service, pass its TailVIP to `--service` so the stable service name, not the physical node name, owns the forwarded ports:

```bash
SERVICE_TAILVIP=100.x.y.z # from Tailscale service settings

sudo tailscale serve --bg --service="$SERVICE_TAILVIP" --http=80 http://127.0.0.1:80
sudo tailscale serve --bg --service="$SERVICE_TAILVIP" --tcp=1935 tcp://127.0.0.1:1935
sudo tailscale serve --bg --service="$SERVICE_TAILVIP" --tcp=8000 tcp://127.0.0.1:8000
sudo tailscale serve --bg --service="$SERVICE_TAILVIP" --tcp=50052 tcp://127.0.0.1:50052
```

## Tailscale ACL Example

Use Tailscale ACLs to restrict who can reach the FluxOmni host. This example allows only members of `group:operators` to reach the UI and media ports.

```json
{
  "groups": {
    "group:operators": ["alice@example.com", "bob@example.com"]
  },
  "acls": [
    {
      "action": "accept",
      "src": ["group:operators"],
      "dst": [
        "tag:fluxomni:80",
        "tag:fluxomni:443",
        "tag:fluxomni:1935",
        "tag:fluxomni:8000",
        "tag:fluxomni:10080"
      ]
    }
  ],
  "tagOwners": {
    "tag:fluxomni": ["group:operators"]
  }
}
```

Then authenticate the server with the tag:

```bash
sudo tailscale up --ssh --advertise-tags=tag:fluxomni
```

If Tailscale SSH works but `http://<tailscale-host>/routes` times out, check the ACLs first. SSH can be allowed while HTTP, RTMP, HLS, and SRT are still blocked; permit at least ports `80`, `1935`, `8000`, and `10080` to the FluxOmni host or tag. If grants already allow the traffic and the ports still time out, use the Tailscale Serve commands above to forward UI, RTMP, and HLS/WebRTC TCP from localhost.

## Remote Media Node over Tailscale

A standalone media node can register to the control plane over the tailnet. Add the media-node host from [Tailscale's Add device page](https://login.tailscale.com/admin/machines/new), join the same tailnet, then run this on the media-node host.

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${CONTROL_TS_HOST:?Set CONTROL_TS_HOST to the control-plane Tailscale IP or MagicDNS name}"
: "${FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN:?Set the same token used by the control plane}"

sudo tailscale up --ssh

MEDIA_TS_IP="$(tailscale ip -4 | head -n1)"

curl -fsSL https://install.fluxomni.io | \
  FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT="http://${CONTROL_TS_HOST}:50052" \
  FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN="$FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN" \
  FLUXOMNI_MEDIA_NODE_PUBLIC_HOST="$MEDIA_TS_IP" \
  FLUXOMNI_MEDIA_NODE_ENDPOINT="http://${MEDIA_TS_IP}:50051" \
  FLUXOMNI_MEDIA_NODE_LABELS="selfhost,tailnet" \
  FLUXOMNI_MEDIA_NODE_ZONE="tailnet" \
  bash -s -- media-node
```

Use the same internal auth token as the control plane. The control-plane RPC port (`50052/tcp`) and media-node gRPC port (`50051/tcp`) only need to be reachable inside the tailnet unless you intentionally run a public distributed fleet.

`50052/tcp` and `50051/tcp` are different directions:

- `50052/tcp` is the control-plane RPC endpoint that media nodes call for registration, heartbeat, and feedback.
- `50051/tcp` is the media-node gRPC endpoint that the control plane calls for media-node operations.

If direct Docker-published ports also time out on the standalone media-node host, run Tailscale Serve there too and advertise the forwarded endpoint:

```bash
# On the standalone media-node host.
sudo tailscale serve --bg --tcp=50051 tcp://127.0.0.1:50051

MEDIA_TS_HOST=media-node.tail380321.ts.net
curl -fsSL https://install.fluxomni.io | \
  FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT="http://${CONTROL_TS_HOST}:50052" \
  FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN="$FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN" \
  FLUXOMNI_MEDIA_NODE_PUBLIC_HOST="$MEDIA_TS_HOST" \
  FLUXOMNI_MEDIA_NODE_ENDPOINT="http://${MEDIA_TS_HOST}:50051" \
  FLUXOMNI_MEDIA_NODE_LABELS="selfhost,tailnet" \
  FLUXOMNI_MEDIA_NODE_ZONE="tailnet" \
  bash -s -- media-node
```

For distributed FluxOmni over Tailscale, keep these TCP paths reachable:

| Host | Port | Purpose |
| --- | --- | --- |
| Control-plane host | `80/tcp` | Control Surface UI/API |
| Control-plane host | `50052/tcp` | Control-plane gRPC for media-node registration |
| Control-plane host with local media node | `1935/tcp` | RTMP ingest |
| Control-plane host with local media node | `8000/tcp` | HLS/WebRTC TCP path |
| Standalone media-node host | `50051/tcp` | Media-node gRPC called by the control plane |
| Standalone media-node host | `1935/tcp` | RTMP ingest |
| Standalone media-node host | `8000/tcp` | HLS/WebRTC TCP path |

Tailscale Serve forwards TCP only. It does not cover SRT UDP (`10080/udp`).

## Cloudflare Tunnel

Cloudflare Tunnel is useful for exposing the Control Surface over HTTPS without opening inbound HTTP ports. It is not a full private L3 network and does not carry RTMP or SRT media ports directly.

Quick UI-only test:

```bash
#!/usr/bin/env bash
set -euo pipefail

curl -fsSL https://install.fluxomni.io | \
  FLUXOMNI_CONTROL_PLANE_HTTP_PORT=127.0.0.1:8080 \
  FLUXOMNI_PUBLIC_HOST=fluxomni.example.com \
  FLUXOMNI_PUBLIC_URL=https://fluxomni.example.com \
  FLUXOMNI_MEDIA_NODE_PUBLIC_HOST="$(hostname -I | awk '{print $1}')" \
  bash

# For a temporary test tunnel. For production, create a named tunnel and route
# fluxomni.example.com to it in Cloudflare Zero Trust.
cloudflared tunnel --url http://127.0.0.1:8080
```

Use Cloudflare Access if you want identity-based protection for the UI. Keep media ports on Tailscale or public firewall rules depending on who must publish and view.

## Choosing an Option

Pick the private-access layer based on which surface needs to be private.

| Option | Best for | Trade-offs |
| --- | --- | --- |
| Tailscale | Private admin, media testing, and remote media nodes | Requires every publisher, viewer, or node to join the tailnet |
| Cloudflare Tunnel | HTTPS UI access without inbound HTTP ports | UI-focused; RTMP/SRT still need Tailscale or public firewall rules |

For most self-host users, start with Tailscale and the single-host install script above. Add Cloudflare Tunnel when you only need browser access to the Control Surface over HTTPS.
