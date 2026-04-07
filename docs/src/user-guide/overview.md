# User Guide

FluxOmni is a web-based RTMP streaming platform that lets you broadcast a single source to multiple destinations simultaneously. The operator interface — called the **Control Surface** — runs in your browser and gives you real-time control over every aspect of your streaming pipeline.

This guide covers the day-to-day operation of the Control Surface after your FluxOmni instance is installed and running. For installation and deployment, see the [Quick Start](../getting-started/quick-start.md) section.

## Key Concepts

**Route** — a named streaming pipeline that connects one ingest input to one or more output destinations. Each route has its own workspace where you manage execution, routing, playlists, and live playback.

**Input** — the ingest endpoint where your source signal arrives. FluxOmni generates a unique URL for each route depending on the chosen protocol (RTMP, SRT, or WebRTC). Point your encoder (OBS, FFmpeg, hardware encoder) at this URL.

**Output** — a destination where FluxOmni relays the ingested signal. Outputs are typically RTMP URLs for platforms like YouTube, Twitch, Facebook Live, or custom CDN endpoints.

**Media Node** — a server that handles the actual media processing (transcoding, relaying, file playback). A single-host install runs one media node automatically. Larger deployments can attach multiple media nodes across different servers.

**Fleet** — the collective view of all attached media nodes, their health, capacity, and cached files.

**Playlist** — a queue of pre-recorded video files that a route can play out through its outputs, useful for scheduled programming or fallback content.

## Control Surface Layout

![Routes list with the navigation menu visible](../images/user-guide/routes-list.jpg)

When you open the Control Surface, you see a persistent sidebar on the left with the FluxOmni logo, version number, and navigation menu. The main content area fills the right side of the screen.

### Operate

- **Attention** — a unified alert feed showing issues across all routes and fleet nodes, sorted by severity (Critical, Attention). Each alert links directly to the affected route.
- **Routes** — the main operational view. Lists all routes with their live status, input/output health, and signal integrity. This is where you spend most of your time.

### Fleet

- **Fleet** — inventory of all media nodes. Shows node health, assignments, heartbeat freshness, reachability, capabilities, and cached file distribution.

### Control

- **Settings** — server-wide configuration including control surface defaults, Google Drive integration, security (password and sign-in posture), and user management.
- **Export / Import** — bulk export or import of route configurations.

### System Metrics

The bottom of the sidebar shows real-time CPU, memory, and network utilization for the control plane.

## Next Steps

- [Routes](routes.md) — learn how to create and operate routes
- [Fleet](fleet.md) — understand media node management
- [Settings](settings.md) — configure your FluxOmni instance
