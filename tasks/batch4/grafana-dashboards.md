# Task: Create Grafana Dashboard JSON Models for API and Infrastructure Monitoring

## Background

The Grafana repository (https://github.com/grafana/grafana) is an open-source visualization and monitoring platform. A new set of provisioned dashboard JSON models is needed for a production web application: an API monitoring dashboard using the RED method (Rate, Errors, Duration), an infrastructure dashboard using the USE method (Utilization, Saturation, Errors), and an SLO compliance dashboard — all with proper templating, thresholds, and alert rules.

## Files to Create/Modify

- `public/dashboards/api-monitoring.json` (create) — Grafana dashboard JSON for API health monitoring with RED metrics
- `public/dashboards/infrastructure.json` (create) — Grafana dashboard JSON for infrastructure resource monitoring with USE metrics
- `public/dashboards/slo-compliance.json` (create) — Grafana dashboard JSON for SLO tracking with error budget visualization
- `public/dashboards/provisioning.yaml` (create) — Grafana provisioning configuration to auto-load all dashboards
- `tests/test_grafana_dashboards.py` (create) — Python tests validating JSON structure, PromQL queries, and panel configuration

## Requirements

### API Monitoring Dashboard (api-monitoring.json)

- Title: "API Monitoring", UID: `api-monitoring`, tags: `["api", "production", "red"]`
- Templating variables:
  - `datasource`: Prometheus data source selector
  - `namespace`: `label_values(http_requests_total, namespace)`
  - `service`: `label_values(http_requests_total{namespace="$namespace"}, service)`
- **Row 1 — Summary stats** (stat panels):
  - Total Request Rate: `sum(rate(http_requests_total{namespace="$namespace", service="$service"}[5m]))`
  - Error Rate %: `(sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100` with thresholds green < 1, yellow < 5, red ≥ 5
  - P95 Latency: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`
  - Active Connections: `sum(http_connections_active{service="$service"})`
- **Row 2 — Time series**:
  - Request Rate by Method: grouped by `method` label
  - Error Rate by Status Code: grouped by `status` label, filtered to 4xx and 5xx
- **Row 3 — Time series**:
  - Latency Percentiles: P50, P95, P99 on the same chart with different colors
  - Request Duration Heatmap: `http_request_duration_seconds_bucket` as a heatmap panel
- **Row 4 — Table**:
  - Top Endpoints: request rate, error rate, P95 latency per endpoint (grouped by `handler` label)
- Refresh: 30s, time range: last 6 hours

### Infrastructure Dashboard (infrastructure.json)

- Title: "Infrastructure", UID: `infrastructure`, tags: `["infra", "use"]`
- Templating variables: `datasource`, `instance` (`label_values(node_cpu_seconds_total, instance)`)
- **Row 1 — Stat panels**: CPU Usage %, Memory Usage %, Disk Usage %, Network I/O
- **Row 2 — Time series**:
  - CPU Utilization: `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` per instance
  - Memory Utilization: `(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100`
- **Row 3 — Time series**:
  - Disk I/O: read/write bytes per second from `node_disk_read_bytes_total` and `node_disk_written_bytes_total`
  - Network Traffic: inbound/outbound from `node_network_receive_bytes_total` and `node_network_transmit_bytes_total`
- **Row 4 — Gauge panels**:
  - CPU Saturation (load average): `node_load1 / count(node_cpu_seconds_total{mode="idle"})` with thresholds at 0.7 and 0.9
  - Disk Space: `(1 - node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100` with threshold at 80%

### SLO Compliance Dashboard (slo-compliance.json)

- Title: "SLO Compliance", UID: `slo-compliance`, tags: `["slo", "sre"]`
- Templating variables: `datasource`, `slo_name`
- **Row 1 — Stat panels**: Current SLO Achievement %, Error Budget Remaining %, Burn Rate (1h)
- **Row 2 — Time series**: SLO achievement over the 28-day rolling window
- **Row 3 — Time series**: Error budget consumption over time (bar gauge showing budget burn)
- **Row 4 — Table**: SLO summary listing all SLOs with target, achievement, budget remaining, status (met/violated)
- Alert rule embedded in the dashboard: fire when error budget remaining drops below 10%

### Provisioning Configuration (provisioning.yaml)

- API version 1
- Provider name: "default", org_id: 1, folder: "Production"
- Type: `file`, options path: `/var/lib/grafana/dashboards`
- `disableDeletion: true`, `updateIntervalSeconds: 60`

### Expected Functionality

- Importing `api-monitoring.json` into Grafana renders a complete API dashboard with interactive variable selectors
- Selecting a different namespace/service using template variables updates all panels
- The error rate stat panel turns red when error rate exceeds 5%
- The infrastructure dashboard shows CPU, memory, disk, and network utilization for selected instances
- The SLO dashboard shows rolling 28-day achievement and error budget burn rate

## Acceptance Criteria

- All dashboard JSON files are valid Grafana dashboard model format with correct `schemaVersion`
- Each dashboard has properly defined templating variables with query types and regex
- PromQL queries in all panels are syntactically correct and use template variables with `$variable` syntax
- Panels use appropriate visualization types: stat, time series, heatmap, gauge, table
- Thresholds are configured with meaningful values and color mappings
- The provisioning YAML is valid and correctly references the dashboard directory
- Tests validate JSON structure, required fields, PromQL patterns, and panel types
