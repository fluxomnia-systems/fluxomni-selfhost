# Changelog

Operator-facing highlights from recent Fluxomni Studio releases.

The changelog is editorial release copy. Use `release-manifest.json` as the factual inventory for dates, module versions, images, and API client refs, but write the latest changelog entry by hand so it reads as operator-facing release notes instead of generated metadata.

## 2026.05.2 (0.13.0) - 29 May 2026

### Per-Output Origin Audio

Each destination can now keep program audio, select a specific track or channel, or drop origin audio before mix-ins are applied. The output editor, GraphQL API, runtime manifest, and media-node FFmpeg planning now share one backend-owned selection contract.

### Learnable Route Baselines

Route media profiles are configurable from Settings and can be learned from observed sources or probed files. Playlist insertion can teach a fresh route from the first valid file, while existing baselines protect routes from incompatible playlist or live-source media.

### Durable Media Library Policy

Artifact storage, playlists, and route workspaces now share durable media-library policy for duplicate imports, private object fetches, derived artifacts, file-operation concurrency, and safe catalog cleanup after backend configuration changes.

### More Compact Operations UI

Route workspace panels, playlist controls, diagnostics, route cards, and sidebar telemetry are tighter and less repetitive. Completed one-shot and sequential playlist items stay marked as played without blocking replay or playlist clearing.

### Public Automation Metadata

`@fluxomni/api-client@0.13.0` is the pinned API client for this release. The self-host docs carry the matching GraphQL schema hash, automation recipes, LLM metadata, and installer version aliases for `v2026.05.2` and `v0.13.0`.

---

## 2026.05.1 (0.12.0) - 20 May 2026

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

## 2026.05.0 (0.11.0) - 6 May 2026

### Shared Media Library

The new Artifacts page gives operators one place to upload files, import Drive assets, tag media by client or show, and reuse the same files across playlists, fallback loops, and route workflows.

### Storage-Aware Uploads

Uploads and imports now surface usable capacity, configured headroom, top consumers, and recent storage rejections before operators start large transfers. Full-storage responses become upload toasts and Attention storage alerts so operators can free space before retrying.

### Cleaner Asset Operations

Bulk tagging, filtered selection, protected deletes, route references, and route-baseline compatibility indicators make larger content libraries safer to manage during live channel operations.

### Stable Release Pins

Public examples now use date-style pins such as `v2026.05.0`, while known core tags remain accepted for direct image pinning. This gives operators a readable stable version to copy into deployment notes and rollback plans.

---

## 2026.04.2 (0.10.2) - 26 April 2026

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

## 2026.04.1 (0.10.1) - 19 April 2026

### Stable Push Token Rotation

Publish credentials now live inside the route spec. Each RTMP, SRT, and WebRTC push ingress gets stable `publish_token` and `internal_namespace` values at creation, and older routes are backfilled automatically. Operators can rotate a token without recreating the route, and import/export preserves the new fields.

### Simplified Fleet Onboarding

The Add Node flow now focuses on the three required environment variables and hides optional settings behind advanced controls. `FLUXOMNI_PUBLIC_URL` can carry the full external scheme, host, and port for proxy deployments. Media nodes unregister cleanly on shutdown so stale nodes disappear immediately. Operators can permanently remove an offline node from Fleet with the new `removeMediaNode` action.

### Immutable Main Build Tags

Successful `main` builds now publish immutable `main-<shortsha>` image tags alongside `edge`. Pin a known main build without rebuilding.

### Smarter Cold-Start Probes

File-ingress ffprobe now uses a 3000 ms per-attempt timeout over 3 attempts with exponential backoff. Cold-start timeouts no longer paint false errors on a healthy publisher in the operator UI.

---

## 0.10.0 - 14 April 2026

### Multi-User Authentication

Named user accounts with per-user passwords, role-based access control (admin and operator roles), configurable session expiry, and self-service password management. WebSocket subscriptions now require authentication too.

### Secure Publish Credentials

Each route gets rotatable `pk_` publish tokens scoped to a specific ingress. Raw stream keys are no longer exposed — operators can rotate or revoke tokens from the route workspace without reconfiguring the route itself.

### Route Ownership

Routes belong to the user who created them. Non-admin operators only see and edit their own routes. Admins can reassign ownership or mark routes as shared from the route modal or the Settings → Users panel.

### Attention Feed

A dedicated alert surface aggregates route-health and fleet-node issues in one place. Operators can dismiss known issues, drill into the affected route or node, and see an all-clear state when everything is healthy.

### Redesigned Operator UI

Compact route cards with structured signal tiles, inline search, density controls, dark/light theme sync, and a unified header across all surfaces. The sidebar is regrouped into Operate, Fleet, and Control sections. Settings moved to dedicated routed pages at `/settings`.

### Low-Latency HLS Preview

Near-real-time in-browser preview with 1-second HLS segments and tighter live-edge sync. Works on Chrome 146+ and all modern browsers. Preview streams are relayed through the control plane so they work behind HTTPS reverse proxies.

### Node Pinning

Routes can be hard-pinned to a specific media node from the route modal. Pinned routes stay unassigned instead of falling back when the selected node is unavailable.

### Graceful Shutdown

The control plane handles SIGINT and SIGTERM cleanly — HTTP connections drain and gRPC calls complete before the process exits. Active streams are not dropped during planned restarts.

---

## 0.9.0 - 13 March 2026

### Distributed Media-Node Orchestration

Standalone media nodes register with the control plane, receive typed execution manifests, and report runtime status back over gRPC. Scale by adding nodes across regions.

### Fleet Monitoring

The `/fleet` surface shows media-node health, route assignments, cached artifacts, and system telemetry (CPU, memory, network). Guided "Add Node" onboarding walks operators through the install command.

### Routes & Fleet Terminology

The operator UI is standardized around Routes (`/routes`) and Fleet (`/fleet`). Legacy dashboard, stream, and client URLs redirect to the canonical pages.

### Durable Assignment Tracking

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
