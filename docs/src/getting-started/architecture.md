# Architecture

Fluxomni Studio runs as separate services: the **frontend**, the
**control-plane**, and one or more **media nodes**.

## Components

### Frontend

The frontend serves the operator UI (Control Surface). In Docker Compose,
it receives public HTTP traffic and forwards API and file requests to the
control-plane through the Docker network.

### Control-plane

The control-plane manages the system. It:

- Serves the GraphQL API and backend HTTP endpoints used by the frontend.
- Manages route definitions, playlist state, user accounts, and settings.
- Assigns routes to media nodes and monitors their health.
- Persists all state to an embedded SQLite database (`data/state.db`).

A single control-plane instance manages the entire fleet. It runs as the
`control-plane` container in the Docker Compose stack.

### Media node

A media node processes and delivers media:

- Receives ingest streams (RTMP push, RTMP pull, SRT push, WebRTC push).
- Relays streams to output destinations (RTMP, RTMPS, SRT, Icecast, file).
- Plays back playlist files through the pipeline.
- Reports health, telemetry, and heartbeat to the control-plane over gRPC.
- Caches playlist files locally for fast playback.

In a single-host install, one media node runs with the control-plane
and communicates through the Docker network. In distributed
deployments, additional media nodes run on separate servers and connect
back to the control-plane over its published gRPC port (TCP 50052).

### SRS (Simple Realtime Server)

Each media node includes an [SRS](https://ossrs.io) instance that handles
the RTMP, HLS, SRT, and WebRTC protocols. Fluxomni Studio
manages SRS configuration and lifecycle automatically. Operators do not
interact with SRS directly.

## Communication

Each media node initiates one authenticated TLS control connection to the control plane, normally on TCP 50052. Runtime commands and feedback travel in opposite directions over that same connection.

- The frontend forwards operator API and file requests to the control plane.
- Fleet issues a one-time enrollment code for a fresh node. The installer saves the machine credential locally and registers only its hash with the control plane.
- Hello/Welcome admits the node's boot and connection generation. Manifest delivery, runtime commands, heartbeat and feedback reuse the outbound connection.
- The control plane never opens a node control connection. A connected private node does not automatically expose public media.
- Artifact bytes use HTTP or durable storage. Internal HTTP artifact tokens are separate from machine admission.

Public RTMP, SRT, HLS and WebRTC access still needs its own advertised media endpoints and reachable ports.

## Route lifecycle

1. An operator creates a route in the Control Surface.
2. The control-plane assigns the route to a media node (auto-placement
   or pinned).
3. The media node receives the route manifest and configures its SRS
   instance.
4. The media node generates ingest endpoints (RTMP, SRT, or WebRTC URLs)
   and reports them back.
5. When a publisher connects, the media node relays the stream to all
   enabled outputs.
6. The control-plane monitors execution state and can reassign the route
   if the media node becomes unhealthy (failover).

## Data storage

All persistent state lives in the `data/` directory:

| Path | Contents |
| ---- | -------- |
| `data/state.db` | Route definitions, settings, user accounts |
| `data/videos/` | Cached playlist files |
| `data/dvr/` | DVR / recording segments (when enabled) |
| `data/srs-http/` | SRS HTTP content directory |

Back up the `data/` directory to preserve your entire configuration.
During runtime, SQLite may also create `state.db-wal` and `state.db-shm` beside `state.db`, so keep the full directory together.
See [Backup & Restore](backup.md) for details.

## Scaling

- **Single host**: One control-plane + one media node on the same server.
  Suitable for small to medium workloads.
- **Distributed**: One control-plane + multiple media nodes on separate
  servers. Each media node handles a subset of routes. The control-plane
  load-balances route assignments across available nodes.
- **Media node capabilities**: Nodes advertise capabilities like
  `PUBLIC_INGEST`, `PUBLIC_EGRESS`, `ARTIFACT_COMPUTE`, and
  `GPU_TRANSCODE`. The scheduler can use these to make placement
  decisions.
