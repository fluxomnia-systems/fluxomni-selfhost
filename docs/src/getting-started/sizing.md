# Server Sizing

Size media nodes by active inputs, outputs, bitrate, and processing mode. A stored route, a live route without destinations, and a route sending twelve outputs have different costs. Current measurements qualify specific workloads, not a universal server maximum.

## Where to run each service

A single host is convenient for a pilot. Budget for the OS, Docker, frontend, control plane, media node, and storage together. The control plane owns API requests, subscriptions, state persistence, and fleet coordination; media nodes run SRS, FFmpeg, ingest, and output delivery.

For production capacity qualification, separate the control plane from media hosts so media pressure does not compete with API and database work. Place test publishers and receivers on other hosts. This is an isolation recommendation, not evidence for a particular control-plane server size or linear scaling across nodes.

Use a stable CPU allocation, sufficient RAM and usable network bandwidth, and persistent storage appropriate to your artifact, playlist, and recording workload. Advertised vCPU count alone is insufficient: record CPU model, cgroup limits, swap, and other tenants. No automatic hardware-derived route or output limit is enforced by this release.

## Measured relay workload: 48 outputs for one hour

On September 27, a pre-release ARM64 Linux development VM sustained **four routes with twelve RTMP outputs each**, using a looping 720p30 H.264/AAC fixture in copy mode and two GraphQL subscribers. The media container alone had a **one-CPU, 2048-MiB limit without swap**. The VM exposed ten CPUs and about 8 GiB RAM; the control plane, test helpers, and unrelated containers shared it.

- **CPU:** media-container p95 was 57.27% of one core; p99 was 70.40%.
- **Memory:** the lifetime cgroup peak, including startup, was 1073.9 MiB. Median charged memory across successive 15-minute windows was 997.7, 996.3, 998.5, and 998.7 MiB.
- **Delivery:** all 48 receivers kept their publisher identities and advanced audio/video counters. There were 719 post-baseline receiver observations across the hour, with a largest sampling gap of 5.60 seconds.
- **Responsiveness:** 720 successful samples each for reads, snapshots, and HLS, with no errors or timeouts. Read/snapshot p95 was 12.30/12.76 ms.
- **Stability:** no media-container restart or cgroup OOM event/kill. The CPU quota still recorded 4539 throttled periods out of 35823 lifetime periods.

The [downloadable evidence summary](../evidence/relay48-2026-09-27.json) includes source revision, Docker image IDs, exact counters, and workload settings. The tested source was `232e1bb2bd7b6513d6e7744b3e77f83ba684a596`; its media runtime changes are included in 26.3.2. These were pre-release images, **not a measurement of the published release image digests**. This report preserves that distinction.

Each receiver averaged about 2.646 Mbit/s, or approximately **127 Mbit/s of aggregate media payload** before additional transport overhead. All media stayed inside Docker networking. This does not measure a physical NIC, provider egress, or Internet delivery. Receiver counters establish progress, not decoded playback quality.

A one-CPU/2-GiB media-container ceiling is not a one-CPU/2-GiB whole-server recommendation. Nor is 48 a maximum or an automatically enforced allowance. Recovery bursts, long-term growth, transcoding, audio mixing, DVR, and alternate route/fan-out shapes need their own qualification.

## What an empty route consumes

An empty route in these experiments means a configured push source with **no publisher, no external outputs, and no preview viewer**. Both disabled routes and enabled routes waiting for a publisher started **zero FFmpeg workers**. The running control plane, media agent, SRS, heartbeats, and telemetry still have a fixed baseline cost.

A separate two-round x86 experiment measured 1, 2, and 10 waiting routes with fresh stacks, 15-second settling, and approximately 30-second sampling windows. Services shared a two-CPU GitHub runner with about 7.75 GiB RAM; the media container was capped at one CPU/2048 MiB. These measurements preceded the later idle-scan optimizations in 26.3.2.

Subtracting each round's mean of its starting and ending zero-route baselines gave these **round 1 / round 2 increments**, not confidence intervals:

- **1 waiting route:** control-plane memory +0.22/+0.14 MiB; media memory −1.34/+0.23 MiB. CPU changed by +0.052/+0.064 percentage points in the control plane and −0.023/−0.017 in the media container.
- **2 waiting routes:** control-plane memory +0.86/+0.64 MiB; media memory −1.08/+0.08 MiB. CPU changed by +0.055/+0.045 and −0.015/−0.066 points, respectively.
- **10 waiting routes:** control-plane memory +2.87/+2.74 MiB; media memory −0.04/+1.68 MiB. CPU changed by +0.106/+0.091 and +0.023/−0.010 points, respectively.

CPU percentages refer to one core. Memory is charged cgroup memory, including cache; it is not whole-host RAM. Negative increments are measurement variation. The media CPU deltas are too small to infer a dependable CPU-per-empty-route coefficient. Ten waiting routes added a few MiB of control-plane state rather than ten media pipelines.

By contrast, **one live RTMP pull route with no external outputs** added 55.32/56.74 MiB and 3.491/3.483 CPU percentage points to the media baseline, with two copy-mode FFmpeg workers. Two live pull routes added 111.22/115.02 MiB and 7.336/7.102 points; ten added 550.76/566.02 MiB and 37.084/37.919 points. Ingest and switching are real media work even before a destination is added.

Source revision: `59a926eacbde786edd0a5a6e36302cfa306c1299`; GitHub run `36306312061`, attempt 1. These short observations do not establish a maximum route count, long-term memory behavior, or active push/transcoding costs.

## Why idle CPU is not zero

Profiling a separate ARM64 workload with 200 waiting routes identified repeated source-authority lookups, manifest copies, and unchanged source scans. The release removes that repeated work while preserving media readiness, source authority, retries, and heartbeat behavior.

In the final local comparison, two quiet 45-second windows measured mean Rust media-agent CPU changing from 0.633% to 0.511% of one core at 200 routes. Total media-container CPU changed from 1.352% to 1.254%. Its zero-route agent baseline after the change was 0.333%. These are short diagnostic point estimates, not confidence bounds or a release-to-release benchmark.

SRS protocol polling and timers, health checks, heartbeats, and state coordination remain active. Full-catalog polling also adds observer cost. An unpublished route should start no media pipeline; a running service still needs background CPU. Do not disable public protocols merely to make an idle graph smaller.

## Qualify your deployment

1. Fix the CPU model, service placement, container limits, image digests, and workload. Count live inputs separately from outputs and record codecs, bitrate, protocols, copy/transcode mode, subscriptions, recording, and playlist activity.
2. Start with a workload below the observed pressure points. Track cgroup CPU, throttling, memory, OOM counters, API latency/errors, heartbeat age, and receiver continuity throughout startup and steady delivery.
3. Estimate network payload as the sum of output bitrates, then include input traffic, transport overhead, preview traffic, and operating reserve. Verify sustained physical egress and provider transfer allowances independently.
4. Soak on your target hardware and exercise simultaneous reconnects, node loss, restart, and failover. Preserve headroom for those events before choosing an operating budget.
5. Increase one workload dimension at a time. Adding media nodes distributes work, but does not establish linear capacity scaling or remove shared control-plane and network constraints.

The exploratory relay experiments used p95 CPU at most 75% of the one-core ceiling and peak RAM at most 75% of the 2-GiB ceiling as candidate headroom checks. These are laboratory selection criteria, not production SLOs or scheduler limits. See [Monitoring](monitoring.md) and [Architecture](architecture.md) for operational context.
