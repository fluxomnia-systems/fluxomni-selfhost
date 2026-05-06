# Roadmap

FluxOmni self-host is built for teams that need dependable live operations under their own control. This roadmap focuses on operator and client outcomes, not internal platform work.

Timelines are intentionally absent because priorities shift with customer deployments, Design Partner feedback, and active production incidents. For the current active backlog, follow the [fluxomni-selfhost issue tracker](https://github.com/fluxomnia-systems/fluxomni-selfhost/issues).

## Available now

The current self-host release covers the production workflows most teams need before adding custom automation.

- **One source to every destination.** Ingest over RTMP, SRT, or WebRTC, then send the same program to RTMP, SRT, and Icecast destinations without per-output software caps.
- **Always-on channel playout.** Run 24/7 channels from local files, Google Drive assets, playlists, or fallback loops so a live route can recover without a manual scramble.
- **Reusable media library.** Upload, import, tag, filter, and reuse artifacts across playlists, fallback loops, and route workflows from the operator UI.
- **Storage-aware operations.** See usable capacity, configured headroom, top consumers, and recent storage rejections before large uploads or imports fail.
- **Fleet and failover visibility.** Add regional media nodes, pin routes when needed, and see route, node, and failover health in the Control Surface and Attention feed.
- **Controlled self-host access.** Run behind public DNS, a reverse proxy, Tailscale, WireGuard, NetBird, or Cloudflare Tunnel, with named operators and role-based access.
- **Pinned, recoverable installs.** Use public date-style release pins such as `v2026.05.0`, rollback with known tags, or track `edge` only when you intentionally want main-branch builds.

## In focus

These are the next product areas being shaped with active users and Design Partners.

- **Production automation.** Schedule route changes, output toggles, playlist boundaries, fallback behavior, and notifications around real stream events.
- **Client-ready media workflows.** Make it easier to organize content by client, show, campaign, or channel, including safer bulk operations and clearer route usage before deleting assets.
- **Recording-to-reuse flow.** Turn live recordings into managed artifacts that can be reviewed, tagged, replayed, or used as fallback content without leaving the platform.
- **Operator handoff polish.** Improve guided setup, copyable endpoint instructions, and status explanations so non-developer operators can run daily workflows confidently.

## On the roadmap

Further out items are larger workflow expansions. Scope and sequencing are still being shaped by deployments.

- **Deeper integrations.** Webhooks, Slack or Teams alerts, object-storage backends, and handoffs into client delivery systems.
- **Distributed media jobs.** Fleet-backed transcode, proxy generation, clip export, and packaging jobs for teams with larger media libraries.
- **Automated highlight generation.** Produce reviewable short clips from long-form source material and route them back into the artifact library.
- **Client workspaces.** Separate operational views, assets, and route templates for agencies or teams serving multiple brands.

## Become a Design Partner

Teams serious about the In Focus and Roadmap areas can join the Platform Early Access program. [Apply via email](mailto:sales@fluxomni.io?subject=Platform%20Early%20Access) with a short description of your use case: current deployment, channels or clients served, the workflows you want automated, and what would unblock your operators.
