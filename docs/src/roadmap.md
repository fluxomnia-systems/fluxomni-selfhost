# Roadmap

Fluxomni Studio self-host is built for teams that need dependable live operations under their own control. This roadmap focuses on operator and client outcomes, not internal platform work.

Timelines are intentionally absent because priorities shift with customer deployments, Design Partner feedback, and active production incidents. For the current active backlog, follow the [fluxomni-selfhost issue tracker](https://github.com/fluxomnia-systems/fluxomni-selfhost/issues).

## Available now

The current self-host release covers the production workflows most teams need before building deeper integrations.

- **One source to every destination.** Ingest over RTMP, SRT, or WebRTC, then send the same program to RTMP, SRT, and Icecast destinations without per-output software caps.
- **Per-destination audio control.** Keep program audio, select a source track or channel, mute origin audio, or apply mix-ins per output while keeping one backend-owned output contract.
- **Always-on channel playout.** Run 24/7 channels from local files, Google Drive assets, playlists, or fallback loops so a live route can recover without a manual scramble.
- **Scheduled playlist starts.** Arm one-shot sequential starts, replay completed queue rows, and keep played state visible without blocking playlist clearing or replay.
- **Reusable media library.** Upload, import, tag, bulk tag, bulk delete, filter, and reuse artifacts across playlists, fallback loops, and route workflows from the operator UI.
- **Storage-aware operations.** See usable capacity, configured headroom, top consumers, recent storage rejections, durable object rows, private fetch URLs, and derived-artifact policy before large uploads or imports fail.
- **Learned media baselines.** Teach route media profiles from real files or observed live sources, save custom profiles, and reject incompatible playlist or live-source media before it reaches the media node.
- **Public automation surface.** Use the stable GraphQL schema, session-aware TypeScript client, generated operations, subscription examples, mutation result payloads, and AI-readable automation recipes for route, playlist, artifact, settings, and Fleet workflows.
- **Fleet and failover visibility.** Add regional media nodes, pin routes when needed, and see route, node, and failover health in the Control Surface and Attention feed.
- **Recording catalog safety.** Recording rows participate in catalog-backed modals and runtime checks, while non-durable DVR files stay cache-like and object-storage rows reject unsafe overwrites.
- **Controlled self-host access.** Run behind public DNS, a reverse proxy, Tailscale, WireGuard, NetBird, or Cloudflare Tunnel, with named operators and role-based access.
- **Pinned, recoverable installs.** Use canonical public release pins such as `v26.2.4`, rollback with known tags, or track `edge` only when you intentionally want main-branch builds.

## In focus

These are the next product areas being shaped with active users and Design Partners.

- **Event-driven automation.** Trigger route changes, output toggles, playlist boundaries, fallback behavior, and notifications from real stream events instead of one-off scripts.
- **Client-ready media workspaces.** Build clearer client, show, campaign, and channel organization on top of the shipped artifact tags, bulk operations, route usage checks, and baseline compatibility signals.
- **Recording-to-reuse flow.** Promote live recordings into managed artifacts that can be reviewed, tagged, replayed, or used as fallback content without leaving the platform.
- **Operator handoff polish.** Improve guided setup, copyable endpoint instructions, and status explanations so non-developer operators can run daily workflows confidently.

## On the roadmap

Further out items are larger workflow expansions. Scope and sequencing are still being shaped by deployments.

- **Deeper integrations.** Webhooks, Slack or Teams alerts, richer storage-provider controls, and handoffs into client delivery systems.
- **Distributed media jobs.** Fleet-backed transcode, proxy generation, clip export, and packaging jobs for teams with larger media libraries.
- **Automated highlight generation.** Produce reviewable short clips from long-form source material and route them back into the artifact library.
- **Client workspaces.** Separate operational views, assets, and route templates for agencies or teams serving multiple brands.

## Become a Design Partner

Teams serious about the In Focus and Roadmap areas can join the Platform Early Access program. [Apply via email](mailto:sales@fluxomni.io?subject=Platform%20Early%20Access) with a short description of your use case: current deployment, channels or clients served, the workflows you want automated, and what would unblock your operators.
