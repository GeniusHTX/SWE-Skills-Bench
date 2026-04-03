# Task: Create Grafana Dashboard JSON Models for Infrastructure Monitoring

## Background

Grafana (https://github.com/grafana/grafana) provides a rich dashboard visualization platform. This task requires creating programmatically generated Grafana dashboard JSON models for monitoring a Kubernetes cluster. The dashboards should cover cluster resource overview, pod-level metrics, and a service golden signals view, using Prometheus as the data source.

## Files to Create/Modify

- `devenv/dashboards/cluster-overview.json` (create) — Dashboard with panels: cluster CPU usage, cluster memory usage, node count, pod count, namespace resource breakdown table.
- `devenv/dashboards/pod-metrics.json` (create) — Dashboard with panels: pod CPU usage, pod memory usage (RSS), container restart count, pod network I/O, OOM kill events. Includes template variable for namespace and pod name filtering.
- `devenv/dashboards/golden-signals.json` (create) — Dashboard with panels per service: request rate, error rate, latency (P50/P95/P99 histogram), saturation (CPU/memory utilization as % of limits). Includes template variables for namespace and service.
- `devenv/dashboards/scripts/generate_dashboard.py` (create) — Python script that generates the above dashboards using a builder pattern. Defines `Panel`, `Row`, `Dashboard` classes that produce valid Grafana JSON.
- `tests/test_grafana_dashboards.py` (create) — Tests validating that generated JSON matches Grafana dashboard schema requirements.

## Requirements

### Cluster Overview Dashboard

- **Row 1 — Cluster Summary** (singlestat/gauge panels):
  - CPU Usage: `sum(rate(container_cpu_usage_seconds_total{container!="POD",container!=""}[5m])) / sum(machine_cpu_cores) * 100` → gauge 0-100%.
  - Memory Usage: `sum(container_memory_working_set_bytes{container!="POD",container!=""}) / sum(machine_memory_bytes) * 100` → gauge.
  - Node Count: `count(kube_node_info)` → stat panel.
  - Pod Count: `sum(kube_pod_info)` → stat panel.
- **Row 2 — Namespace Breakdown** (table panel):
  - Columns: namespace, CPU request sum, CPU limit sum, memory request sum, memory limit sum, pod count.
  - Query: `sum by (namespace)(kube_pod_container_resource_requests{resource="cpu"})` etc.
- Datasource: `Prometheus` (uid `prometheus`).
- Time range: last 6 hours, refresh every 30s.

### Pod Metrics Dashboard

- Template variables:
  - `$namespace`: query `label_values(kube_pod_info, namespace)`.
  - `$pod`: query `label_values(kube_pod_info{namespace="$namespace"}, pod)`, multi-select enabled.
- **Panels**:
  - CPU: `sum(rate(container_cpu_usage_seconds_total{namespace="$namespace",pod=~"$pod",container!="POD"}[5m])) by (pod)` → time series.
  - Memory: `sum(container_memory_working_set_bytes{namespace="$namespace",pod=~"$pod",container!="POD"}) by (pod)` → time series with unit `bytes`.
  - Restarts: `sum(kube_pod_container_status_restarts_total{namespace="$namespace",pod=~"$pod"}) by (pod)` → time series with `last` value shown.
  - Network I/O: receive `sum(rate(container_network_receive_bytes_total{namespace="$namespace",pod=~"$pod"}[5m])) by (pod)` and transmit query → two-series time series.
  - OOM Kills: `sum(kube_pod_container_status_last_terminated_reason{reason="OOMKilled",namespace="$namespace"}) by (pod)` → stat panel.

### Golden Signals Dashboard

- Template variable `$service`: query `label_values(http_requests_total, service)`.
- **Request Rate**: `sum(rate(http_requests_total{service="$service"}[5m]))` → time series, unit `reqps`.
- **Error Rate**: `sum(rate(http_requests_total{service="$service",status=~"5.."}[5m])) / sum(rate(http_requests_total{service="$service"}[5m])) * 100` → time series, unit `%`, threshold: yellow > 1%, red > 5%.
- **Latency**: `histogram_quantile(0.50, ...)`, same for 0.95 and 0.99 → three stacked time series, unit `ms`.
- **Saturation**: CPU `sum(rate(container_cpu_usage_seconds_total{...}[5m])) / sum(kube_pod_container_resource_limits{resource="cpu"}) * 100`, memory similar → two panels.

### Dashboard Generator Script

- `Panel(title, panel_type, targets, **options)` — creates a panel dict with Grafana-compatible JSON fields.
- `Row(title, panels)` — groups panels into a row.
- `Dashboard(title, uid, rows, variables=[], refresh="30s")` — assembles the full dashboard JSON with `schemaVersion: 39`, `editable: true`, `panels` with `gridPos` auto-layout.
- Auto-assigns `id` to each panel incrementally.
- `to_json()` → pretty-printed JSON string.

### Expected Functionality

- The cluster overview JSON, when imported into Grafana, displays 4 summary gauges and 1 table panel.
- Pod metrics JSON shows template variable dropdowns for namespace and pod.
- Golden signals JSON shows request rate, error rate with color thresholds, and latency percentiles.
- `generate_dashboard.py` when executed produces all three JSON files.

## Acceptance Criteria

- All three JSON files are valid Grafana dashboard models with correct `schemaVersion`, `uid`, and `panels` arrays.
- Every panel has a `datasource` reference, valid `targets` with PromQL `expr`, and appropriate `unit` in `fieldConfig`.
- Template variables use correct `label_values` queries.
- The golden signals dashboard includes color thresholds on the error rate panel.
- The dashboard generator script produces JSON matching the handcrafted files.
- Tests validate JSON structure, panel count, required fields, and PromQL expression syntax.
