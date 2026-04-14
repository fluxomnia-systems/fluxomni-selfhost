# Monitoring

FluxOmni provides built-in system metrics in the Control Surface sidebar
and supports exporting traces via OpenTelemetry (OTLP).

## Built-in metrics

The bottom of the Control Surface sidebar shows real-time gauges for the
control-plane host:

- **CPU** — current processor utilization percentage.
- **MEM** — current memory utilization percentage.
- **NET** — current network throughput.

These values update in real time and give operators a quick health check
without leaving the UI.

## Fleet telemetry

The [Fleet](../user-guide/fleet.md) page shows per-node telemetry:

- **Heartbeat** — time since the last heartbeat from each media node.
  A stale heartbeat (configurable via
  `FLUXOMNI_MEDIA_NODE_STALE_HEARTBEAT_SECS`) indicates the node may
  be unreachable.
- **Worker** — active worker process count.
- **Assignments** — number of routes placed on the node.
- **Cache** — number of cached playlist files.
- **Reachability** — whether the node is publicly reachable.
- **Scheduling** — whether the node accepts new work.

## Attention feed

The **Attention** page (`/attention`) aggregates alerts across all routes
and fleet nodes. Alert severity levels:

- **CRITICAL (HIGH)** — route probe errors, offline nodes, or failures
  that prevent playback.
- **ATTENTION (MEDIUM)** — parameter mismatches or degraded conditions
  that may affect quality.

## OpenTelemetry (OTLP)

FluxOmni can export traces to an OpenTelemetry collector. Set the
endpoint in `.env`:

```bash
FLUXOMNI_OTLP_ENDPOINT=http://collector.example.com:4318
```

Then restart:

```bash
docker compose up -d
```

This sends traces over HTTP (OTLP/HTTP) to the specified collector.
From there, you can forward data to backends like Jaeger, Grafana Tempo,
or Datadog.

### Example: Grafana + Tempo

A minimal collector setup using Grafana Alloy or the OpenTelemetry
Collector:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: "0.0.0.0:4318"

exporters:
  otlp:
    endpoint: "tempo:4317"
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [otlp]
```

Point `FLUXOMNI_OTLP_ENDPOINT` at the collector's HTTP receiver.

## Log management

By default, FluxOmni logs to stdout which Docker captures. View logs
with:

```bash
docker compose logs -f control-plane media-node
```

To write logs to files on the host, set:

```bash
FLUXOMNI_WRITE_LOGS_TO_FILE=true
```

Log files are written to the data directory. Use `FLUXOMNI_LOG_FORMAT`
to switch between `pretty` (human-readable) and `json` (structured)
output.

## Health checks

The control-plane and media-node containers include Docker health checks.
Check container health with:

```bash
docker compose ps
```

A healthy stack shows all services as `Up (healthy)`.
