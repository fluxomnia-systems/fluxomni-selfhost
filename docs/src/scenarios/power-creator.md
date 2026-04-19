# Power creator beyond SaaS caps

## Who this is for

Individual creators and small teams streaming to 4+ platforms simultaneously who keep hitting SaaS tier walls ($80–$300+/mo). You want a fixed monthly cost, unlimited destinations, and full control of your data.

## What you'll build

Single-host FluxOmni on a small cloud VM (Hetzner CPX21, €5–10/mo). OBS on your desk pushes RTMP to FluxOmni, which fans out to YouTube, Twitch, Kick, Facebook, and any custom RTMP endpoint.

```text
OBS → FluxOmni (single VM) → { YouTube, Twitch, Kick, Facebook, Custom RTMP }
```

## Setup

1. Provision a small cloud VM. See [Deployment guides](../deployment/overview.md).
2. Install: `curl -fsSL https://install.fluxomni.io | bash`.
3. Open the control surface, create a single route, add platform outputs.
4. Point OBS at the route's publish URL — FluxOmni fans it out to every platform.

## Cost and scale notes

Fixed €5–15 per month of infra replaces $100+/mo of SaaS fees. Copy-through fan-out is nearly free on CPU, so a small VM handles all five destinations comfortably. For a custom domain and TLS, see [Reverse proxy & TLS](../getting-started/reverse-proxy.md).

## Next steps

- [Routes — editing and outputs](../user-guide/routes.md)
- [Reverse proxy & TLS](../getting-started/reverse-proxy.md)
- [Monitoring](../getting-started/monitoring.md)
