# Roadmap

This page separates current Fluxomni Studio features from planned work. Use the available features to assess the product today; planned items do not have delivery dates.

We do not list dates because priorities change with customer deployments, Design Partner feedback, and production incidents. For current work, see the [fluxomni-selfhost issue tracker](https://github.com/fluxomnia-systems/fluxomni-selfhost/issues).

## Available now

The current self-host release supports these production workflows:

- **One source to every destination.** Ingest over RTMP, SRT, or WebRTC, then send the program to RTMP, SRT, and Icecast destinations. There is no software output-count cap; capacity depends on your servers and network.
- **Per-destination audio control.** Keep program audio, select a source track or channel, mute origin audio, or apply mix-ins for each destination.
- **Always-on channel playout.** Run 24/7 channels from local files, Google Drive assets, playlists, or fallback loops so a live route can recover without manual action.
- **Scheduled playlist starts.** Arm one-shot sequential starts, replay completed queue rows, and keep played state visible without blocking playlist clearing or replay.
- **Reusable media library.** Upload, import, tag, bulk tag, bulk delete, filter, and reuse artifacts across playlists, fallback loops, and route workflows from the operator UI.
- **Storage-aware operations.** Check usable capacity, configured headroom, files using the most space, and recent storage rejections before large uploads or imports fail. Inspect durable object records, private fetch URLs, and the derived-artifact policy.
- **Learned media baselines.** Create route media profiles from files or live sources and save custom profiles. Reject incompatible playlist or live-source media before it reaches the media node.
- **Public automation API.** Use the stable GraphQL schema, session-aware TypeScript client, generated operations, subscription examples, mutation result payloads, and AI-readable automation recipes for route, playlist, artifact, settings, and Fleet workflows.
- **Fleet and failover visibility.** Add regional media nodes, pin routes when needed, and see route, node, and failover health in the Control Surface and Attention feed.
- **Recording catalog safety.** Recording records appear in catalog dialogs and runtime checks. Non-durable DVR files are treated as cache, and object-storage records reject unsafe overwrites.
- **Controlled self-host access.** Run behind public DNS, a reverse proxy, Tailscale, WireGuard, NetBird, or Cloudflare Tunnel, with named operators and role-based access.
- **Pinned, recoverable installs.** Use canonical public release pins such as `v26.2.4`, plan recovery with matching state and images, or track `edge` only when you intentionally want main-branch builds.

## In focus

We are planning these areas with active users and Design Partners.

- **Event-driven automation.** Trigger route changes, output toggles, playlist boundaries, fallback behavior, and notifications from real stream events instead of one-off scripts.
- **Client-ready media workspaces.** Organize media by client, show, campaign, and channel using existing artifact tags, bulk operations, route usage checks, and baseline compatibility status.
- **Recording-to-reuse flow.** Save live recordings as managed artifacts. Review, tag, replay, or use them as fallback content within the platform.
- **Clearer operator handoffs.** Improve guided setup, endpoint instructions, and status explanations so operators can manage daily work without development experience.

## On the roadmap

These larger additions are planned for later. Their scope and order depend on deployment needs.

- **Deeper integrations.** Webhooks, Slack or Teams alerts, more storage-provider controls, and connections to client delivery systems.
- **Distributed media jobs.** Transcoding, proxy generation, clip export, and packaging jobs across the fleet for teams with larger media libraries.
- **Automated highlight generation.** Create short clips from long recordings for review and save them in the artifact library.
- **Client workspaces.** Separate operational views, assets, and route templates for agencies or teams serving multiple brands.

## Become a Design Partner

Teams that need the In Focus and Roadmap features can join the Platform Early Access program. [Apply via email](mailto:sales@fluxomni.io?subject=Platform%20Early%20Access) with a short description of your use case: current deployment, channels or clients served, the workflows you want to automate, and what your operators need.
