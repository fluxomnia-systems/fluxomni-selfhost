# Changelog

Operator-facing highlights from recent FluxOmni releases.

## 2026.04.2 — April 2026

### Clearer Live Route Status

Routes now use the media-node lifecycle as the source of truth. The Control Surface shows Pending, Converging, LIVE, Paused, and Error states so operators can distinguish startup, healthy playback, intentional pauses, and failures without relying on lossy aggregate booleans.

### Cleaner Route Identity Model

FluxOmni now completes the migration away from legacy `RestreamKey`, `IngressKey`, `restream_key`, and `ingress_key` fields. Current exports use route IDs, labels, `publish_token`, and `internal_namespace`; older imported specs are still upgraded automatically before state is materialized.

> **Upgrade note:** external clients or automations that still read or submit the removed key fields must move to the current route ID and publish-token fields before upgrading.

### Playlist and Output Stability

Playlist lifecycle callbacks now flow through the same runtime-event path as push ingresses, reducing false stopped-state flicker between files. Same-owner placement updates preserve route presentation continuity, and enabling outputs no longer flaps a healthy route through transient Pending states.

### Quieter, Safer Media-Node Logs

Routine manifest reconciliation, file-download churn, and expected FFmpeg/SRS lifecycle messages stay below operator warning level. Playlist probes no longer create RTMP probe storms, and media-node artifact download logs redact userinfo, query strings, and fragments from fetch URLs.

### No Telemetry Unless Enabled

Self-hosted webapp builds no longer initialize PostHog by default. Analytics only run when both `VITE_POSTHOG_ENABLED=true` and a non-empty `VITE_POSTHOG_KEY` are provided at build time, preserving the no-telemetry promise for standard self-host installs.

### Date-Style Version Pins

Public release examples now use date-style pins such as `v2026.04.2`. During the migration, the installer accepts both date-style pins and legacy semantic pins such as `v0.10.2`, mapping known date releases to the matching legacy image tag when needed.

---

## 2026.04.1 — April 2026

### Stable Push Token Rotation

Publish credentials now live inside the route spec. Each RTMP, SRT, and WebRTC push ingress gets stable `publish_token` and `internal_namespace` values at creation, and older routes are backfilled automatically. Operators can rotate a token without recreating the route, and import/export preserves the new fields.

### Simplified Fleet Onboarding

The Add Node flow now focuses on the three required environment variables and hides optional settings behind advanced controls. `FLUXOMNI_PUBLIC_URL` can carry the full external scheme, host, and port for proxy deployments. Media nodes unregister cleanly on shutdown so stale nodes disappear immediately. Operators can permanently remove an offline node from Fleet with the new `removeMediaNode` action.

### Immutable Main Build Tags

Successful `main` builds now publish immutable `main-<shortsha>` image tags alongside `edge`. Pin a known main build without rebuilding.

### Smarter Cold-Start Probes

File-ingress ffprobe now uses a 3000 ms per-attempt timeout over 3 attempts with exponential backoff. Cold-start timeouts no longer paint false errors on a healthy publisher in the operator UI.

---

## 0.10.0 — April 2026

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

## 0.9 — March 2026

### Distributed Media-Node Orchestration

Standalone media nodes register with the control plane, receive typed execution manifests, and report runtime status back over gRPC. Scale by adding nodes across regions.

### Fleet Monitoring

The `/fleet` surface shows media-node health, route assignments, cached artifacts, and system telemetry (CPU, memory, network). Guided "Add Node" onboarding walks operators through the install command.

### Routes & Fleet Terminology

The operator UI is standardized around Routes (`/routes`) and Fleet (`/fleet`). Legacy dashboard, stream, and client URLs redirect to the canonical pages.

### Durable Assignment Tracking

Route-to-node assignments persist across control-plane restarts with per-resource epochs. Stale ownership updates from disconnected nodes cannot override newer placement decisions.
