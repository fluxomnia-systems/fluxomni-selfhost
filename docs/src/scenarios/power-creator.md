# Power creator beyond SaaS caps

## Who this is for

Individual creators and small teams streaming to 4+ platforms at once who face SaaS plan limits ($80–$300+/mo). Use your own server for a fixed monthly cost, unlimited destinations, and full control of your data.

## What you'll build

A single-host Fluxomni Studio install on a small cloud VM (Hetzner CPX21, €5–10/mo). OBS sends RTMP to Fluxomni Studio, which sends the stream to YouTube, Twitch, Kick, Facebook, and custom RTMP endpoints.

```text
OBS → Fluxomni Studio (single VM) → { YouTube, Twitch, Kick, Facebook, Custom RTMP }
```

## Setup

1. Provision a small cloud VM. See [Deployment guides](../deployment/overview.md).
2. Install: `curl -fsSL https://install.fluxomni.io | bash`.
3. Complete [First Stream](../getting-started/first-stream.md) to create a protected operator account, route, and first output.
4. Set OBS to use the route's publish URL. Fluxomni Studio sends the stream to every platform.

## Cost and scale notes

Infrastructure costs €5–15 per month instead of $100+/mo in SaaS fees. Sending copy-through streams to several outputs uses little CPU, so a small VM can handle all five destinations. For a custom domain and TLS, see [Reverse proxy & TLS](../getting-started/reverse-proxy.md).

## Next steps

- [Routes — editing and outputs](../user-guide/routes.md)
- [Reverse proxy & TLS](../getting-started/reverse-proxy.md)
- [Monitoring](../getting-started/monitoring.md)
