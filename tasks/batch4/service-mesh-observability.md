# Task: Build a Service Mesh Observability Dashboard Configuration for Linkerd2

## Background

The Linkerd2 repository (https://github.com/linkerd/linkerd2) is a lightweight service mesh for Kubernetes. A new observability configuration package is needed that sets up Prometheus scraping for Linkerd proxy metrics, defines recording rules for the golden signals (latency, traffic, errors, saturation), creates Grafana dashboard JSON models for per-service and mesh-wide views, and implements alert rules for SLO-based thresholds — providing a complete monitoring stack for a meshed application.

## Files to Create/Modify

- `viz/observability/prometheus/scrape-config.yaml` (create) — Prometheus scrape configuration for Linkerd proxy metrics
- `viz/observability/prometheus/recording-rules.yaml` (create) — Recording rules for pre-computed golden signal metrics
- `viz/observability/prometheus/alerting-rules.yaml` (create) — Alert rules for SLO violations and error budget consumption
- `viz/observability/grafana/mesh-overview.json` (create) — Grafana dashboard JSON for mesh-wide overview (request rate, error rate, latency by service)
- `viz/observability/grafana/service-detail.json` (create) — Grafana dashboard JSON for single-service deep dive (per-route metrics, TCP connections, retry rates)
- `tests/test_service_mesh_observability.py` (create) — Python tests validating YAML/JSON structure and PromQL correctness

## Requirements

### Prometheus Scrape Configuration

- Job `linkerd-proxy`: scrapes Linkerd proxy metrics from pods with annotation `linkerd.io/proxy-inject: enabled`
- Kubernetes SD config with role `pod`, relabel to filter by annotation
- Scrape interval: 15s, scrape timeout: 10s
- Metrics path: `/metrics`, port: 4191 (Linkerd admin port)
- Job `linkerd-controller`: scrapes Linkerd control plane from `linkerd` namespace, port 9995

### Recording Rules

Group `linkerd_golden_signals` (interval 30s):
- `linkerd:request_rate:5m` — `sum(rate(request_total{direction="inbound"}[5m])) by (deployment, namespace)`
- `linkerd:success_rate:5m` — `sum(rate(request_total{direction="inbound", classification="success"}[5m])) by (deployment, namespace) / sum(rate(request_total{direction="inbound"}[5m])) by (deployment, namespace)`
- `linkerd:latency_p50:5m` — `histogram_quantile(0.5, sum(rate(response_latency_ms_bucket{direction="inbound"}[5m])) by (le, deployment, namespace))`
- `linkerd:latency_p95:5m` — same as P50 but quantile 0.95
- `linkerd:latency_p99:5m` — same but quantile 0.99
- `linkerd:tcp_open_connections` — `sum(tcp_open_connections{direction="inbound"}) by (deployment, namespace)`

### Alert Rules

Group `linkerd_alerts`:
- `LinkerdHighErrorRate`: `linkerd:success_rate:5m < 0.99` for 5m, severity critical, summary "Service {{ $labels.deployment }} success rate below 99%"
- `LinkerdHighLatency`: `linkerd:latency_p99:5m > 500` for 5m, severity warning, summary "Service {{ $labels.deployment }} P99 latency above 500ms"
- `LinkerdHighTraffic`: `linkerd:request_rate:5m > 1000` for 10m, severity info
- `LinkerdProxyDown`: `up{job="linkerd-proxy"} == 0` for 2m, severity critical

### Mesh Overview Dashboard (mesh-overview.json)

- Title: "Service Mesh Overview"
- Templating variable: `namespace` (query: `label_values(request_total, namespace)`)
- Row 1 — Summary stats (stat panels): total request rate, overall success rate, average P50 latency, active TCP connections
- Row 2 — Time series: request rate per service, error rate per service
- Row 3 — Time series: P50/P95/P99 latency per service
- Row 4 — Table: service list with current request rate, success rate, P99 latency
- Refresh: 30s, timezone: browser

### Service Detail Dashboard (service-detail.json)

- Title: "Service Detail"
- Templating variables: `namespace`, `deployment`
- Row 1 — Stat panels: request rate, success rate, P99 latency, TCP connections for the selected service
- Row 2 — Time series: inbound vs outbound request rates
- Row 3 — Heatmap: response latency distribution
- Row 4 — Time series: retry rate, TCP connection open/close rates
- Row 5 — Table: per-route metrics (route name, request rate, success rate, P99)

### Expected Functionality

- Prometheus scrapes Linkerd proxy metrics from all meshed pods every 15 seconds
- Recording rules pre-compute golden signal metrics aggregated by deployment and namespace
- Alert fires when any service's success rate drops below 99% for 5 minutes
- Mesh overview dashboard shows all services' health at a glance with drill-down navigation to the detail dashboard
- Service detail dashboard shows per-route metrics and latency distribution for a selected service

## Acceptance Criteria

- Prometheus scrape config correctly targets Linkerd proxy pods using Kubernetes SD and annotation-based filtering
- Recording rules produce valid PromQL and are grouped with a 30-second evaluation interval
- Alert rules have correct expressions, for-durations, and labels/annotations
- Grafana dashboard JSON files are valid, contain correct PromQL queries, and use templating variables
- Mesh overview includes stat panels, time series, and a table with per-service health
- Service detail includes heatmaps, per-route tables, and inbound/outbound traffic views
- Tests validate YAML/JSON structure, PromQL syntax, and dashboard panel configuration
