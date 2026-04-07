# Routes

Routes are the core of FluxOmni. Each route is an independent streaming pipeline with its own ingest input, one or more outputs, an optional playlist, and a live playback monitor.

## Routes List

Navigate to **Routes** in the sidebar (or visit `/routes`) to see all configured routes. The list page provides:

- **Summary bar** — total live inputs, live outputs, and active alerts at a glance.
- **Search** — filter routes by name, input label, or output label.
- **Scope toggle** — switch between viewing **Inputs** or **Outputs** to focus on ingest health or distribution state.
- **View mode** — choose **Compact** (dense list) or **Expanded** (full route cards with inline controls).

### Controls Tab

The Controls tab on the routes list shows three health panels:

- **Inputs / Route health** — per-route input status broken down by Offline, Starting, LIVE, and Degraded.
- **Signal Integrity** — highlights mismatch and fetch issues across all routes without needing to open each one individually.
- **Outputs / Distribution state** — per-route output status with the same Offline / Starting / LIVE / Degraded breakdown.

### Routes Tab

Switches to a flat list view of all routes with their current state.

## Creating a Route

Click **+ New Route** on the routes list page (or the **Create Route** prompt on an empty instance) to open the route setup dialog.

![The Create Route dialog with identity, source, and routing options](../images/user-guide/create-route.jpg)

The dialog walks you through three sections:

### 1. Route Identity

- **Route Label** — a human-readable name for the route (e.g. "Main broadcast").
- **Route Key** — a URL-safe stream key used in the ingest URL. This key becomes part of the ingest endpoint (e.g. `rtmp://<your-host>/main/primary`).

### 2. Primary Live Source

Choose the ingest protocol for this route:

- **RTMP** — the most common protocol, compatible with OBS, FFmpeg, and most hardware encoders.
- **SRT** — Secure Reliable Transport, a low-latency protocol designed for unreliable networks.
- **WebRTC** — browser-based ingest for ultra-low-latency workflows.

Then select the **Primary Source Mode**:

- **Accept publish** — the route listens for incoming streams (push mode). FluxOmni generates a publish address on the assigned media node.
- **Pull from remote** — the route pulls a stream from a remote URL (pull mode). Provide the source URL and FluxOmni will fetch it.

### 3. Advanced Routing

Expand this section to configure placement, failover, live backups, and file fallback. Defaults are auto-placement with system failover, which works well for most setups.

Click **Create route** to save. The route appears in the list and is immediately assigned to a media node.

## Route Workspace

Click **Open workspace →** on any route card to enter the route workspace.

![The route workspace showing execution status, signal path, and workspace tabs](../images/user-guide/route-workspace.jpg)

The workspace header shows the route name, status badge (Starting / Live / Offline), stream key, input and output counts, and issue count. Quick actions include **Edit route** and **Export route**.

The workspace has four tabs:

### Execution

Shows the current execution status of the route, including the state badge and active issue count.

### Routing

The signal path view, showing the full pipeline:

- **Input** — the ingest endpoint with its current status (Awaiting source, Receiving, etc.). Each input has a toggle to enable/disable it, a copy button for the ingest URL, and protocol badge (RTMP, SRT, WebRTC).
- **Outputs** — all configured output destinations. Each output shows its destination URL, protocol badge, individual enable/disable toggle, and status indicator.
- **+ Add output** — button to add a new output destination to the route.
- **Outputs master toggle** — enables or disables all outputs at once.
- **Filter outputs** — search within the outputs list when you have many destinations.

### Playlist

A file-based playback queue for pre-recorded content:

- **Now playing** — the currently active file with codec info (e.g. h264, 1280x720, 25fps, aac, 1ch), a progress bar, and transport controls (previous, play/pause, next, loop toggle).
- **Status bar** — shows playlist readiness, local file count, mismatched files, and stream errors.
- **Google Drive integration** — paste a Google Drive folder or file ID/URL, then click **Load files** to import content. Use **Start all downloads** to pull files to the media node.
- **File list** — each file shows codec and resolution details, duration, and a signal integrity badge: **REF** (reference match), **DIFF** (parameter mismatch), or **ERROR** (probe failure). Click **Preview** to inspect any file.
- **Clear playlist** — removes all files from the queue.

### Live Playback

An in-browser HLS monitor for the route's live output. When the media node has a playback URL configured and the route is live, you can watch the output stream directly in the Control Surface. Shows a message when the playback URL is not yet ready or not configured.

## Alerts

Route-level alerts appear in the **Alerts** badge on the routes list and in the **Attention** page.

![The Attention page showing route and fleet alerts](../images/user-guide/attention.jpg)

Alert severity levels:

- **CRITICAL (HIGH)** — stream probe errors in playlist files that will prevent playback.
- **ATTENTION (MEDIUM)** — mismatched stream parameters in playlist files that may cause quality or compatibility issues.

Click **Open route** on any alert to jump directly to the affected route workspace.
