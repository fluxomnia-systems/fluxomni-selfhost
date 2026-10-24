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

Compare the full cost of the server, transfer allowance, storage, and any commercial license with the plan you use today. A low server price alone does not establish a saving. Use the [measured sizing guide](../getting-started/sizing.md) and test your bitrate and destinations.

For a custom domain and TLS, see [Reverse proxy & TLS](../getting-started/reverse-proxy.md). Check [licensing and support](https://fluxomni.io/#pricing) before using the installation for paid or client work.

## Next steps

- [Routes — editing and outputs](../user-guide/routes.md)
- [Reverse proxy & TLS](../getting-started/reverse-proxy.md)
- [Monitoring](../getting-started/monitoring.md)
