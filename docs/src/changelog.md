# Changelog

Operator-facing highlights from recent Fluxomni releases.

The changelog is editorial release copy. Use `release-manifest.json` as the factual inventory for dates, module versions, images, and API client refs, but write the latest changelog entry by hand so it reads as operator-facing release notes instead of generated metadata.

## v26.4.0 - 6 November 2026

This release adds reusable rundowns, richer playlist programming, recording retention, and a per-node capacity ledger. Upgrade the frontend, control plane, and every media node together. See the [upgrade guide](getting-started/upgrade-26.4.0.md). `v26.3.2` predates the capacity-ledger contract.

### Recordings and DVR retention

Finalized FLV recordings can be preserved as independent Library assets, with visible progress and cancellation. Preserved files stay usable in playlists after the recording node is gone. Linux media nodes can rotate continuous recordings into independently finalized segments. Interrupted segments never become playable sources.

Active outputs can opt into age and byte retention, with one budget across current and historical recording nodes. Archive ownership survives reassignment and restart. Unavailable archives defer deletion and show retry failures. The Fluxomni web app shows loading, empty, retry, and deletion states, and the Library preview plays FLV recordings, including on HTTPS pages. Downloads stream through the authenticated control plane. Administrators can find historical recordings after a route is removed.

Publishers wait for the previous process to exit before restarting, so recordings finalize cleanly and SRS streams do not overlap.

**API change:** list recordings through the artifact library by kind and output ID, and delete them by file ID. The filename-only DVR query and removal mutation are removed.

### Rundowns

The Fluxomni web app has a Rundowns page for reusable program rundowns. Operators can edit and duplicate media order, and apply an exact saved revision from a route playlist when the route is idle and has no schedule. Viewers get read-only access.

Repeated clips keep their own placement identity through playback, cueing, timing, and completion history. The editor previews planned duration, offsets, and the finite total with the same timing calculation as route playlists. Saved references protect Library assets and recordings from deletion. Revision checks reject stale saves and applies. Unsaved edits are protected when you leave the page, switch rundowns, or reload saved data.

### Playlist stingers, timing, and schedules

Playlists can add an optional stinger clip from the artifact library. Sequential playback inserts it between completed content files. Manual controls skip it, and a failed stinger warns and continues. Recovery controls stay usable when a recording stinger is unavailable. Imports reject new unavailable stinger references.

The playlist shows planned item durations, cumulative offsets, scheduled start and end times, and a finite program total. Unknown durations and loops stay marked as uncertain. Times show their zone and UTC offset. Start a playlist file at an exact timestamp from the progress line or by editing the elapsed time. Progress starts only after the new playback is confirmed.

Routes can schedule playlist starts every day or on selected weekdays in an IANA time zone. The route shows the next start and the last confirmed, skipped, blocked, or failed occurrence, with pause, resume, and explicit replacement of one-shot schedules. Durable admission prevents duplicate starts across repeated ticks and restarts. DST gaps are skipped, repeated times fire once, and missed starts have a five-minute grace period. Existing one-shot starts survive the upgrade.

### Playlist preparation

Prepare playlist files ahead of playback into reusable H.264/AAC MPEG-TS variants that match the route baseline, including custom dimensions, fractional frame rates, and audio settings. The picker prepares selected files and the current queue together. Originals and incoming live streams are not changed. Playback waits for the complete queue, and verified preparation clears baseline mismatch alerts.

Operators can give preparation its own Linux CPU, memory, and task budget while live video stays outside it. Fleet shows utilization, limits, and waiting work. If configured isolation is unavailable, preparation does not run unbounded. Media nodes report cgroup setup at startup so the installer can verify enforcement. See [Offline Preparation Resource Limits](getting-started/configuration.md#offline-preparation-resource-limits).

### Slideshows and thumbnails

Create reusable slideshow videos from PNG and JPEG images in the Library or the artifact picker. Order the photos, keep the five-second defaults or adjust names and timing, then preview, download, or reuse the finished MP4. Rendering publishes verified MP4 files to configured S3-compatible storage. Finished videos keep working after input deletion or render-node loss. Object storage is checked before composition.

Small thumbnails are generated for stable uploaded videos and preserved recordings, and shown in the Library and the shared file picker. Loading, unsupported, and retry states keep playback controls, selection, and pagination working. Thumbnails inherit the visibility of their source and are removed when that asset is deleted.

### Route readiness

Routes show a compact readiness checklist for live, playlist, and relay flows. It lists prerequisites, stale or unavailable evidence, and links to the controls that fix each finding. It can preview placement and capacity rules without starting streams.

### Per-node capacity ledger

Administrators can set per-node route and output ceilings in Fleet and see starting, committed, and retiring demand. Route and output growth, imports, and placement reserve capacity atomically. A slot is released only after FFmpeg exit is proved and recorded.

**Upgrade:** installations that already have running or assigned execution must follow [Capacity Ledger Upgrades](getting-started/capacity-upgrades.md) on the first boot of this release. Stop old execution containers and initialize the ledger before starting media. The installer verifies global shutdown, persists initialization, and removes its temporary acknowledgement before media starts. Later upgrades require disabled routes and zero reservations. Automatic updates stop before that inspection. `v26.3.2` does not provide this contract.

### Private media nodes

Private media nodes can open an authenticated TLS control connection to the control plane, with no inbound control port or VPN. Fleet shows control connection state separately from media access. Fleet generates one copy-and-run command that enrolls a node with a short-lived, one-time code. The installer downloads only over HTTPS. Admins can rotate, recover, and revoke node credentials while keeping the node ID and archive ownership. Revocation does not release reserved capacity.

Fleet can also repair one cached relay-backed source on an explicitly isolated media node. Repair keeps source files and live playback intact.

### Google Drive service accounts

Administrators can connect a Google Drive service account under Settings → Artifacts → Connections and import shared private videos, or the videos directly inside a folder. Public API-key imports still work, with an explicit choice when both methods are configured. Credentials are encrypted and kept out of settings exports. Removing them keeps downloaded artifacts.

### Native MCP and Fluxomni Connect

Native MCP remains a preview. v26.4.0 can use the same verified issuer identity to sign in to the Fluxomni web app and to approve MCP clients. Approved clients can read the current user, visible routes, and flow readiness. An opt-in management scope can manage routes, Library files, playlists, and outputs, still under the current user's permissions. See [Native MCP access](api/mcp.md). Startup fails if MCP is configured without the matching browser client in `FLUXOMNI_OIDC_CONFIG`.

Connected apps can register this Installation with Fluxomni Connect and give named accounts personal read access for AI clients. A named local Admin owns registration. Personal read access needs a separate browser approval for the exact client. See [Fluxomni Connect](getting-started/connect.md).

### Relational storage

Identities, Connected apps approvals, node credentials, rundowns, slideshows, playlists and schedules, preparation, thumbnails, recording preservation and archives, admission limits, and execution ownership now live in checked relational SQLite tables. Existing data is kept, and state changes commit together with their operator history. One SQLite baseline handles fresh installs and direct upgrades from released schema 11. Do not start an older release on a database this release has migrated.

A change-history API returns stable sequence pages for operators and administrators, with declared coverage and redaction of protected values. History is bounded by a one-day age target and a 512 MiB soft size target. Undo commands and history screens are not part of this release.

### API and sign-in

`@fluxomni/api-client@26.4.0` is the pinned API client. GraphQL POST requests must use `application/json`. WebSocket connections that do not initialize within ten seconds are closed. The legacy password mutation is removed; use user creation, password rotation, and session logout. Slideshow mutations require a request ID. A retry returns the original command receipt, and the slideshow field is the current record.

Browser sessions last 24 hours by default. Installations that already saved a session TTL keep it, and `0` still disables expiry. Reverse-proxy deployments must set `FLUXOMNI_TRUSTED_PROXY_IPS` to the exact proxy IPs, and proxies must append or replace client-address headers. Without that setting, clients behind a proxy share one login limit.

Live subscription connections close when their session expires, logs out, or loses authority after a password, role, or user change.

---

## v26.3.2 - 27 September 2026

This release reduces repeated control-plane and idle media-node work, bounds artifact catalog requests, and makes output startup status reflect media progress. See the [upgrade guide](getting-started/upgrade-26.3.2.md) for deployment and API changes.

### Control-Plane Responsiveness

SQLite persistence runs behind bounded work queues, and slow node delivery is isolated from other nodes. Route updates copy less unrelated state, while artifact metadata probes have concurrency and time limits. Delivery receipts remain attached to work already in flight so a newer update does not misreport an earlier operation's result.

### Quieter Idle Routes

Media nodes share immutable manifests and reuse unchanged source scans. A push route waiting for a publisher starts no FFmpeg worker. Background service activity remains, so an idle stack does not use zero CPU. The [sizing guide](getting-started/sizing.md) explains the measured costs for 1, 2, and 10 empty routes and the follow-up CPU investigation.

### Bounded Artifact Libraries

Library browsing now uses filtered, sorted pages, and file subscriptions target transfers, one route, or one file. Playlist metadata and route projections avoid repeated full-catalog work. **API change:** `artifacts.libraryFiles` returns a page object, and the full-catalog `artifacts` subscription is removed. Update custom queries and subscription consumers before upgrading.

### Media Startup and Recovery

Outputs become LIVE after FFmpeg reports positive media progress; stalled startup is bounded by a deadline. SRS is pinned to 7.0.165 to include the upstream admission-race fix. This is an upstream SRS 7 alpha build; validate your RTMP, SRT, and WebRTC workflows when upgrading.

### Workload-Specific Sizing Evidence

A pre-release, single-host ARM64 experiment sustained 48 RTMP copy outputs across four routes for one hour with a one-CPU/2-GiB media-container limit. This is a measured workload, not a whole-server specification or a maximum output count. See the [method, results, and limitations](getting-started/sizing.md).

---

## v26.3.1 - 14 September 2026

### Source-Session Contract Upgrade

Upgrade the control plane and media nodes together: source sessions now require canonical RouteSourceId, private node contract 4, and protobuf v2. Independent source sessions preserve verified publishers across manifest refreshes and agent recovery, reject obsolete feedback, and prevent stopped sessions from reviving.

### Recoverable Live Connections

WebSocket connections keep retrying recoverable failures and report healthy only after active queries refresh. Unexpected subscription completion reconnects without discarding stale data; fatal closures remain visibly disconnected.

### Program Playback and Relay Controls

Program supports low-latency WebRTC playback with automatic HLS fallback and a standalone player. Relay / Distribution workspaces expose safe playback and ingest endpoints, clearer viewer counts, grouped sessions, and per-session controls. Program playback enforces route ownership — named users cannot play another user's private route.

### Quarterly Release Versions

Packages, runtime images, releases, and public manifests share canonical `vYY.Q.P` versions. Historical releases remain discoverable through their original core versions.

### Media-Node Compatibility and Crash Recovery

Fleet reports unknown, outdated, and ahead node contracts and blocks incompatible execution. Crash recovery reaps orphan processes, exposes exhausted restart budgets, restarts failed background tasks, and recovers overloaded feedback through heartbeats. Cache cleanup protects live artifacts and reports manifest health.

### Safer Settings Import and Export

Exports include route-owner metadata without creating accounts on import. Preview validates owner references, supports explicit username remapping to local users, and provides clearer summaries and reliable copying on HTTP LAN deployments.

### Clearer Operator Workspaces

Routes, Settings, and Fleet use compact layouts, consistent access rules, and clearer keyboard and touch controls. Recording actions stay accessible beside long URLs, while diagnostics show backend-reported startup, stopping, HLS preparation, and live or playlist source details.

### Hardened API and Runtime Boundaries

Media-node RPCs now require the shared bearer token outside loopback. GraphQL operations require explicit authorization guards, internal errors return safe client messages, and CI detects unguarded resolvers.

### Reliable State Persistence

Related state changes commit atomically before becoming visible in memory. Ordinary updates write only changed rows within one guarded operation, reducing contention and preventing detached writes.

### Runtime Tracing and Metrics

OpenTelemetry traces follow requests from the control plane to media nodes. The OTLP pipeline also reports API latency, manifest sync, FFmpeg restarts, artifact jobs, heartbeats, and background-task health with bounded metric labels.

### Reliable Live Takeover

Catalog synchronization preserves accepted live-stream statistics, preventing eligible publishers from falling back to files or stalling at baseline checks. Eligible preferred pulls retry while fallback keeps playing and regain selection only after verified readiness.

### Public Automation Metadata

`@fluxomni/api-client@26.3.1` is the pinned API client for this release. The self-host docs carry the matching GraphQL schema hash, automation recipes, LLM metadata, and installer version aliases for `v26.3.1`.

---

## v26.2.4 (0.13.0) - 29 May 2026

### Per-Output Origin Audio

Each destination can now keep program audio, select a specific track or channel, or drop origin audio before mix-ins are applied. The output editor, GraphQL API, runtime manifest, and media-node FFmpeg planning now share one backend-owned selection contract.

### Learnable Route Baselines

Route media profiles are configurable from Settings and can be learned from observed sources or probed files. Playlist insertion can teach a fresh route from the first valid file, while existing baselines protect routes from incompatible playlist or live-source media.

### Durable Media Library Policy

Artifact storage, playlists, and route workspaces now share durable media-library policy for duplicate imports, private object fetches, derived artifacts, file-operation concurrency, and safe catalog cleanup after backend configuration changes.

### More Compact Operations UI

Route workspace panels, playlist controls, diagnostics, route cards, and sidebar telemetry are tighter and less repetitive. Completed one-shot and sequential playlist items stay marked as played without blocking replay or playlist clearing.

### Public Automation Metadata (v0.13.0)

`@fluxomni/api-client@0.13.0` is the pinned API client for this release. The self-host docs carry the matching GraphQL schema hash, automation recipes, LLM metadata, and installer version aliases for `v26.2.4` and `v0.13.0`.

---

## v26.2.3 (0.12.0) - 20 May 2026

### Stable Automation Surface

Public GraphQL automation now uses Route and Artifacts vocabulary across the schema, generated operations, TypeScript client, webapp callers, Playwright helpers, and repo-owned operator tooling. Control planes expose the active SDL at `/api/schema.graphql`, so scripts and integrations can discover the live contract outside debug mode.

### Recipes and Session-Aware Client

`@fluxomni/api-client@0.12.0` exposes generated documents, raw GraphQL execution, and session-aware transport helpers. The public docs now cover session login, desired-state route convergence, route-source controls, playlist and artifact settings, Fleet command safety, subscriptions, and error helpers.

### API-Visible Route Telemetry

Automation and operators can read clearer source freshness, bitrate, viewer activity, and availability signals through the API and Control Surface. Playlist route workflows also expose baseline mismatch details through Attention and route workspace issue affordances, so automations can converge routes without scraping UI state.

### Split Frontend Image

The web UI now has its own image alongside the control-plane and media-node images. This makes reverse-proxy and split-runtime deployments easier to reason about while preserving the embedded control-plane UI as a fallback.

### Safer Playlist Automation

Playlist routes can teach or enforce media baselines, reject incompatible live or playlist sources earlier, and surface mismatch details through Attention and route workspace issue affordances. Automations can converge routes against these states without scraping UI-only signals.

---

## v26.2.2 (0.11.0) - 6 May 2026

### Shared Media Library

The new Artifacts page gives operators one place to upload files, import Drive assets, tag media by client or show, and reuse the same files across playlists, fallback loops, and route workflows.

### Storage-Aware Uploads

Uploads and imports now surface usable capacity, configured headroom, top consumers, and recent storage rejections before operators start large transfers. Full-storage responses become upload toasts and Attention storage alerts so operators can free space before retrying.

### Cleaner Asset Operations

Bulk tagging, filtered selection, protected deletes, route references, and route-baseline compatibility indicators make larger content libraries safer to manage during live channel operations.

### Stable Release Pins

Public examples now use quarterly pins such as `v26.2.2`, while known core tags remain accepted for direct image pinning. This gives operators a readable stable version to copy into deployment notes and rollback plans.

---

## v26.2.1 (0.10.2) - 26 April 2026

### Clearer Live Route Status

Routes now use the media-node lifecycle as the source of truth. The Control Surface shows Pending, Converging, LIVE, Paused, and Error states so operators can distinguish startup, healthy playback, intentional pauses, and failures without relying on lossy aggregate booleans.

### Cleaner Route Identity Model

Fluxomni Studio now completes the migration away from legacy `RestreamKey`, `IngressKey`, `restream_key`, and `ingress_key` fields. Current exports use route IDs, labels, `publish_token`, and `internal_namespace`; older imported specs are still upgraded automatically before state is materialized.

> **Upgrade note:** external clients or automations that still read or submit the removed key fields must move to the current route ID and publish-token fields before upgrading.

### Playlist and Output Stability

Playlist lifecycle callbacks now flow through the same runtime-event path as push ingresses, reducing false stopped-state flicker between files. Same-owner placement updates preserve route presentation continuity, and enabling outputs no longer flaps a healthy route through transient Pending states.

### Quieter, Safer Media-Node Logs

Routine manifest reconciliation, file-download churn, and expected media lifecycle messages stay below operator warning level. Playlist probes no longer create noisy feedback loops, and media-node artifact download logs redact userinfo, query strings, and fragments from fetch URLs.

### No Telemetry Unless Enabled

Self-hosted webapp builds no longer initialize PostHog by default. Analytics only run when both `VITE_POSTHOG_ENABLED=true` and a non-empty `VITE_POSTHOG_KEY` are provided at build time, preserving the no-telemetry promise for standard self-host installs.

---

## v26.2.0 (0.10.1) - 19 April 2026

### Stable Push Token Rotation

Publish credentials now live inside the route spec. Each RTMP, SRT, and WebRTC push ingress gets stable `publish_token` and `internal_namespace` values at creation, and older routes are backfilled automatically. Operators can rotate a token without recreating the route, and import/export preserves the new fields.

### Simplified Fleet Onboarding

The Add Node flow now focuses on the three required environment variables and hides optional settings behind advanced controls. `FLUXOMNI_PUBLIC_URL` can carry the full external scheme, host, and port for proxy deployments. Media nodes unregister cleanly on shutdown so stale nodes disappear immediately. Operators can permanently remove an offline node from Fleet with the new `removeMediaNode` action.

### Immutable Main Build Tags

Successful `main` builds now publish immutable `main-<shortsha>` image tags alongside `edge`. Pin a known main build without rebuilding.

### Smarter Cold-Start Probes

File-ingress ffprobe now uses a 3000 ms per-attempt timeout over 3 attempts with exponential backoff. Cold-start timeouts no longer paint false errors on a healthy publisher in the operator UI.

---

## v26.1.0 (0.10.0 / 0.9.0) - 14 April 2026

This combined public release identity covers the first modern Fluxomni Studio milestones from March and April 2026. The installer resolves `v26.1.0` to the newer `v0.10.0` runtime, while `v0.9.0` remains available as a direct rollback tag.

### Core 0.10.0 - 14 April 2026

#### Multi-User Authentication

Named user accounts with per-user passwords, role-based access control (admin and operator roles), configurable session expiry, and self-service password management. WebSocket subscriptions now require authentication too.

#### Secure Publish Credentials

Each route gets rotatable `pk_` publish tokens scoped to a specific ingress. Raw stream keys are no longer exposed — operators can rotate or revoke tokens from the route workspace without reconfiguring the route itself.

#### Route Ownership

Routes belong to the user who created them. Non-admin operators only see and edit their own routes. Admins can reassign ownership or mark routes as shared from the route modal or the Settings → Users panel.

#### Attention Feed

A dedicated alert surface aggregates route-health and fleet-node issues in one place. Operators can dismiss known issues, drill into the affected route or node, and see an all-clear state when everything is healthy.

#### Redesigned Operator UI

Compact route cards with structured signal tiles, inline search, density controls, dark/light theme sync, and a unified header across all surfaces. The sidebar is regrouped into Operate, Fleet, and Control sections. Settings moved to dedicated routed pages at `/settings`.

#### Low-Latency HLS Preview

Near-real-time in-browser preview with 1-second HLS segments and tighter live-edge sync. Works on Chrome 146+ and all modern browsers. Preview streams are relayed through the control plane so they work behind HTTPS reverse proxies.

#### Node Pinning

Routes can be hard-pinned to a specific media node from the route modal. Pinned routes stay unassigned instead of falling back when the selected node is unavailable.

#### Graceful Shutdown

The control plane handles SIGINT and SIGTERM cleanly — HTTP connections drain and gRPC calls complete before the process exits. Active streams are not dropped during planned restarts.

### Core 0.9.0 - 13 March 2026

#### Distributed Media-Node Orchestration

Standalone media nodes register with the control plane, receive typed execution manifests, and report runtime status back over gRPC. Scale by adding nodes across regions.

#### Fleet Monitoring

The `/fleet` surface shows media-node health, route assignments, cached artifacts, and system telemetry (CPU, memory, network). Guided "Add Node" onboarding walks operators through the install command.

#### Routes & Fleet Terminology

The operator UI is standardized around Routes (`/routes`) and Fleet (`/fleet`). Legacy dashboard, stream, and client URLs redirect to the canonical pages.

#### Durable Assignment Tracking

Route-to-node assignments persist across control-plane restarts with per-resource epochs. Stale ownership updates from disconnected nodes cannot override newer placement decisions.

---

## Ephyr Restreamer predecessor — 2021-2024

Fluxomni Studio continues the Ephyr Restreamer line. The predecessor releases established the single-host restreaming model, GraphQL control API, dashboard operations, deployment scripts, and media-server integrations that later evolved into Fluxomni routes, fleet nodes, artifacts, and operator automation.

### Restreamer 0.8.0 — November 4, 2024

The final released Ephyr Restreamer line expanded playlist-oriented workflows, made playlists optional per restream, added playback encoding work, and introduced drag-and-drop ordering for inputs and outputs. It also improved memory and network statistics, moved images to GitHub Container Registry, updated FFmpeg to 6.0, updated SRS to v5-r3, switched GraphQL subscriptions to `graphql-ws`, and extracted shared GraphQL and SRS client code into reusable crates.

### Restreamer 0.7.0 — April 17, 2023

Restreamer 0.7.0 added dashboard-wide Start All and Stop All controls, last command and error visibility, password-state indicators, input-stream information, file-backup playback metadata, Google Drive link normalization, input endpoint reordering, and server CPU-core visibility. Deployment gained default port opening, OpenTelemetry collector configuration, allowed-IP controls, and optional state clearing on restart. Runtime work moved logging to `tracing`, added OpenTelemetry trace support, updated SRS to v4.0-r4, and routed SRS and FFmpeg logs through the same tracing pipeline.

### Restreamer 0.6.0 — October 2, 2022

Restreamer 0.6.0 expanded audio mixing and backup workflows. Outputs could use up to three TeamSpeak mixers, specify TeamSpeak identity, apply sidechain behavior, and change delay smoothly. Inputs gained multiple backups per input, clearer primary and playback naming, keyboard-friendly label editing, and more visible endpoint labels. The release also introduced graceful FFmpeg shutdown, FIFO-based mixer feeding, FFmpeg 5.1, SRS v4.0-r1, Ubuntu 20.04 images, Rust 1.64, Tokio v1, Actix v4, and broader frontend tooling updates.

### Restreamer 0.5.0 — April 20, 2022

Restreamer 0.5.0 focused on dashboard operations and deployment portability. Operators gained CPU, memory, and network statistics, dashboard filters, export and import, title-bar connection-loss indication, search by label, and clearer input-number status markers. Deployments could be sourced from a custom Docker registry, and the embedded SRS server moved to v4.

### Restreamer 0.4.0 — November 27, 2021

Restreamer 0.4.0 introduced the dashboard application, Docker-based deployment, VScale support, custom input labels, multiple-JSON input mode, preview links for broadcasts, public mixer output pages, YouTube preview embeds, copy buttons for input and output URLs, unstable status reporting, and a broader GraphQL schema with settings, IDs, and longer input keys. It also fixed several early operator-facing UI issues, including lingering errors, stale active inputs after deletion, wrong output indication, long-label trimming, and volume resets during output edits.

### Restreamer 0.3.0 — May 11, 2021

Restreamer 0.3.0 added operator settings for server title and deletion confirmation, dashboard-level Start All and Stop All controls, input and output counts, bounded copyable error messages, and matching GraphQL settings mutations and subscriptions.

### Restreamer 0.2.0 — March 18, 2021

Restreamer 0.2.0 reworked the original API around unified restream objects, import and export specs, backup endpoints, HLS endpoints and HLS pulling, output editing, DVR file management, and richer output destinations including TeamSpeak, MP3, Icecast, SRT, and local FLV recording. Deployment automation added Ubuntu 20.04 provisioning, optional firewalld setup, mounted-volume detection for DigitalOcean and Hetzner Cloud, and Oracle Cloud Infrastructure documentation.

### Restreamer 0.1.2 — February 13, 2021

Restreamer 0.1.2 fixed incorrect default registry selection in the Ubuntu 20.04 provisioning script.

### Restreamer 0.1.1 — February 5, 2021

Restreamer 0.1.1 fixed the broken GraphQL Playground in debug mode.

### Restreamer 0.1.0 — January 26, 2021

The initial Ephyr Restreamer release shipped the core web UI, GraphQL API, Docker image, Ubuntu provisioning script, DigitalOcean and Hetzner deployment guides, RTMP push and pull inputs, output fan-out, online and offline status indicators, enable and disable actions, and optional Basic HTTP authentication.
