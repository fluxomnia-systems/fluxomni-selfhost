# Architecture

Fluxomni Studio uses a split runtime with the **frontend**, the
**control-plane**, and one or more **media nodes**.

## Components

### Frontend

The frontend serves the operator UI (Control Surface). In Docker Compose,
it is the public HTTP entrypoint and proxies API/file requests back to the
control-plane over Docker-internal networking.

### Control-plane

The control-plane is the brain of the system. It:

- Serves the GraphQL API and backend HTTP endpoints used by the frontend.
- Manages route definitions, playlist state, user accounts, and settings.
- Assigns routes to media nodes and monitors their health.
- Persists all state to an embedded SQLite database (`data/state.db`).

A single control-plane instance manages the entire fleet. It runs as the
`control-plane` container in the Docker Compose stack.

### Media node

A media node handles the actual media work:

- Receives ingest streams (RTMP push, RTMP pull, SRT push, WebRTC push).
- Relays streams to output destinations (RTMP, RTMPS, SRT, Icecast, file).
- Plays back playlist files through the pipeline.
- Reports health, telemetry, and heartbeat to the control-plane over gRPC.
- Caches playlist files locally for fast playback.

In a single-host install, one media node runs alongside the control-plane
and communicates over Docker-internal networking. In distributed
deployments, additional media nodes run on separate servers and connect
back to the control-plane over its published gRPC port (TCP 50052).

### SRS (Simple Realtime Server)

Each media node embeds an [SRS](https://ossrs.io) instance that provides
the low-level RTMP, HLS, SRT, and WebRTC protocol handling. Fluxomni Studio
manages SRS configuration and lifecycle automatically. Operators do not
interact with SRS directly.

## Communication

```text
┌──────────────┐    HTTP :80     ┌─────────────────┐    gRPC :50052    ┌─────────────────┐
│   Frontend   │◄──────────────► │  Control-plane  │◄────────────────► │   Media Node 1  │
│  - UI/API    │                 │  - API          │    gRPC :50051    │  - RTMP :1935   │
│  proxy       │                 │  - State mgmt   │◄────────────────► │  - SRT  :10080  │
└──────────────┘                 │  - Scheduling   │                   │  - HLS  :8000   │
                                 │                 │    gRPC :50051    └─────────────────┘
                                 │                 │◄──────────────┐
                                 └─────────────────┘               │    ┌─────────────────┐
                                                                   └──► │   Media Node 2  │
                                                                        │  (remote host)  │
                                                                        └─────────────────┘
```

- **Frontend to control-plane**: The frontend serves the Control Surface
  and proxies API/file requests to the control-plane over Docker-internal
  HTTP.
- **Control-plane to media node**: The control-plane pushes route
  manifests, playlist updates, and scheduling decisions to media nodes
  over gRPC.
- **Media node to control-plane**: Each media node sends periodic
  heartbeats, telemetry (CPU, memory, network), and execution state
  updates back to the control-plane.
- **Auth token**: Both services share
  `FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN`. This token authenticates
  gRPC calls in both directions.

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
