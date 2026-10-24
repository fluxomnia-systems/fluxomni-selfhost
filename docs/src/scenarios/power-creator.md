# Power creator beyond SaaS caps

## Who this is for

Creators and small teams that want to stream to several platforms from their own server. Fluxomni does not impose an output-count cap. The usable output count depends on bitrate, processing mode, and server and network capacity.

## What you'll build

A single-host Fluxomni Studio install. OBS sends one RTMP feed to Fluxomni Studio, which relays it to YouTube, Twitch, Kick, Facebook, or custom RTMP endpoints.

```text
OBS → Fluxomni Studio (single VM) → { YouTube, Twitch, Kick, Facebook, Custom RTMP }
```

## Setup

1. Provision a small cloud VM. See [Deployment guides](../deployment/overview.md).
2. Install: `curl -fsSL https://install.fluxomni.io | bash`.
3. Complete [First Stream](../getting-started/first-stream.md) to create a protected operator account, route, and first output.
4. Set OBS to use the route's publish URL. Fluxomni Studio sends the stream to every platform.

## Cost and scale notes

Plan outgoing bandwidth from your stream bitrate and destination count. For one 6-Mbit/s feed, these are payload estimates:

| Destinations | Outgoing media payload | Basis |
| --- | --- | --- |
| 3 | ~18 Mbit/s | 3 × 6 Mbit/s |
| 5 | ~30 Mbit/s | 5 × 6 Mbit/s |
| 12 | ~72 Mbit/s | 12 × 6 Mbit/s |

Add input traffic, protocol overhead, previews, and operating reserve. These are bandwidth calculations, not CPU measurements. Use the [relay sizing table](../getting-started/sizing.md) to compare media budgets, then test your input and destination count.

Compare the server, transfer allowance, storage, and any commercial license with the plan you use today.

For a custom domain and TLS, see [Reverse proxy & TLS](../getting-started/reverse-proxy.md). Check [licensing and support](https://fluxomni.io/#pricing) before using the installation for paid or client work.

## Next steps

- [Routes — editing and outputs](../user-guide/routes.md)
- [Reverse proxy & TLS](../getting-started/reverse-proxy.md)
- [Monitoring](../getting-started/monitoring.md)
