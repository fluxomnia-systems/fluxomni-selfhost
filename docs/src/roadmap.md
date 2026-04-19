# Roadmap

FluxOmni is built as a distributed media operations framework. This page describes what's shipping today, what's actively in development, and what's on the longer-term roadmap.

Timelines are intentionally absent — priorities shift with Design Partner feedback and active incidents. For the current active backlog, follow the [fluxomni-selfhost issue tracker](https://github.com/fluxomnia-systems/fluxomni-selfhost/issues).

## Shipping now

The capabilities available in the current self-host release.

- **Live multistreaming.** Ingest over RTMP, SRT, or WebRTC and fan out to unlimited RTMP / SRT / Icecast destinations through copy-through pipelines.
- **Linear channel playback.** Run 24/7 channels from a playlist of local or Google Drive files, with file-backup loops as an automatic safety net.
- **Distributed fleet.** Control plane plus one or more regional media nodes with automatic ingress failover across primary, backup, file-backup, and playlist sources.
- **DVR recording.** SRS-based recording for later use, with HLS live preview for operators.

## Coming

In active development. Design Partners shape priorities and get early access.

- **Asset ingest and media catalog.** Upload, tag, search, and reuse media assets across routes without juggling folders on disk.
- **Distributed render jobs.** Offload encode, transcode, and clip-generation tasks across the fleet instead of pinning them to a single host.
- **Event-driven automation workflows.** Trigger routes, outputs, and notifications based on stream events (start, offline, failover, schedule boundaries).

## On the roadmap

Further out. Priorities and scope are still being shaped.

- **AI-powered clip assembly.** OpusClip-style automated highlight generation from long-form source material, integrated with the asset catalog.
- **Deeper integrations.** Slack notifications, webhook pipelines, object-storage backends for assets and recordings.

## Become a Design Partner

Teams serious about the Coming and Roadmap features can join the Platform Early Access program. [Apply via email](mailto:sales@fluxomni.io?subject=Platform%20Early%20Access) with a short description of your use case — current deployment, the workflows you want automated, and what would unblock your team.
