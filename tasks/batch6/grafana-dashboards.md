# Task: Build Grafana Dashboards for an API Platform and Infrastructure Monitoring

## Background

An API platform serving 12 microservices needs three production Grafana dashboards: a high-level executive overview, a per-service deep dive following the RED method, and an infrastructure dashboard following the USE method. Each dashboard must be provisioned as JSON, use Prometheus as the datasource, and include template variables for interactive filtering.

## Files to Create/Modify

- `grafana/dashboards/executive-overview.json` (create) — Executive dashboard with aggregated platform health, revenue metrics, and SLO compliance
- `grafana/dashboards/service-red.json` (create) — Per-service RED method dashboard (Rate, Errors, Duration) with route-level breakdown
- `grafana/dashboards/infrastructure-use.json` (create) — Infrastructure USE method dashboard (Utilization, Saturation, Errors) for nodes, pods, and databases
- `grafana/provisioning/dashboards.yaml` (create) — Dashboard provisioning configuration pointing to dashboard JSON files
- `grafana/provisioning/datasources.yaml` (create) — Datasource provisioning for Prometheus and PostgreSQL

## Requirements

### Executive Overview Dashboard (`grafana/dashboards/executive-overview.json`)

- Title: `"Platform Executive Overview"`, uid: `"exec-overview"`, tags: `["executive", "platform"]`.
- Refresh interval: `30s`.
- Template variables:
  - `$environment`: values `production`, `staging` (label filter on all queries).
  - `$time_range`: custom time range override (1h, 6h, 24h, 7d).

**Row 1 — Platform Health (4 stat panels):**
- **Total RPS**: `sum(rate(http_requests_total{env="$environment"}[5m]))`. Thresholds: green >100, yellow >500, red >1000.
- **Global Error Rate**: `sum(rate(http_requests_total{status=~"5..", env="$environment"}[5m])) / sum(rate(http_requests_total{env="$environment"}[5m])) * 100`. Unit: percent. Thresholds: green <1%, yellow <5%, red >=5%.
- **P95 Latency (ms)**: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{env="$environment"}[5m])) by (le)) * 1000`. Unit: ms. Threshold: green <500, yellow <1000, red >=1000.
- **Active Users (15m)**: `sum(increase(user_sessions_active_total{env="$environment"}[15m]))`.

**Row 2 — SLO Compliance (1 bar gauge panel):**
- Bar gauge showing SLO compliance percentage per service.
- Query: `slo:service_availability:ratio_28d{env="$environment"} * 100`.
- Min: 95, Max: 100. Thresholds: red <99, yellow <99.9, green >=99.9.
- Orientation: horizontal. Display labels: true.

**Row 3 — Traffic Trends (2 timeseries panels):**
- **Requests Over Time**: timeseries, `sum(rate(http_requests_total{env="$environment"}[5m])) by (service)`, legend per service, stacked.
- **Error Rate Over Time**: timeseries, `sum(rate(http_requests_total{status=~"5..", env="$environment"}[5m])) by (service) / sum(rate(http_requests_total{env="$environment"}[5m])) by (service) * 100`. Override: error threshold line at 1%.

**Row 4 — Revenue Impact (2 panels):**
- **Successful Payments/min**: `sum(rate(payments_completed_total{env="$environment"}[5m])) * 60`. Unit: ops/min.
- **Failed Payments/min**: `sum(rate(payments_failed_total{env="$environment"}[5m])) * 60`. Alert threshold at >5 failures/min.

### Service RED Dashboard (`grafana/dashboards/service-red.json`)

- Title: `"Service RED Metrics"`, uid: `"service-red"`, tags: `["service", "red"]`.
- Template variables:
  - `$namespace`: multi-select, query `label_values(http_requests_total, namespace)`.
  - `$service`: dependent on namespace, query `label_values(http_requests_total{namespace="$namespace"}, service)`.
  - `$interval`: custom, values `1m`, `5m`, `15m`.

**Row 1 — Summary Stats (3 stat panels):**
- **Request Rate**: `sum(rate(http_requests_total{service="$service", namespace="$namespace"}[$interval]))`. Unit: req/s.
- **Error Rate %**: error count / total * 100. Unit: percent.
- **P95 Latency**: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service="$service", namespace="$namespace"}[$interval])) by (le)) * 1000`. Unit: ms.

**Row 2 — Rate (2 timeseries panels):**
- **Requests by Status Code**: `sum(rate(http_requests_total{service="$service", namespace="$namespace"}[$interval])) by (status)`. Color overrides: 2xx green, 3xx blue, 4xx yellow, 5xx red.
- **Requests by Route**: `sum(rate(http_requests_total{service="$service", namespace="$namespace"}[$interval])) by (handler)`. Top 10 by value.

**Row 3 — Errors (2 panels):**
- **Error Rate Over Time**: timeseries with threshold at 1% and 5%.
- **Error Breakdown Table**: table panel showing `handler`, `status`, `count`, sorted by count desc. Columns: handler, status code, error count (last 1h), percentage of total errors.

**Row 4 — Duration (3 panels):**
- **Latency Heatmap**: heatmap panel, query `sum(increase(http_request_duration_seconds_bucket{service="$service", namespace="$namespace"}[$interval])) by (le)`. Color scheme: spectral.
- **Latency Percentiles**: timeseries overlaying P50, P95, P99 latencies.
- **Slowest Routes**: table panel ranking routes by P95 latency, top 10.

**Row 5 — Dependencies (1 panel):**
- **Upstream Request Rate**: `sum(rate(http_client_requests_total{source_service="$service"}[$interval])) by (target_service, status)`. Shows which services this service calls and error rates of those calls.

### Infrastructure USE Dashboard (`grafana/dashboards/infrastructure-use.json`)

- Title: `"Infrastructure USE Metrics"`, uid: `"infra-use"`, tags: `["infrastructure", "use"]`.
- Template variables: `$node`, `$namespace`.

**Row 1 — Cluster Summary (4 stat panels):**
- **Total Nodes**: `count(kube_node_info)`.
- **Total Pods Running**: `sum(kube_pod_status_phase{phase="Running"})`.
- **Cluster CPU Usage %**: `(1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))) * 100`.
- **Cluster Memory Usage %**: `(1 - sum(node_memory_MemAvailable_bytes) / sum(node_memory_MemTotal_bytes)) * 100`.

**Row 2 — Node Resources (3 timeseries panels):**
- **CPU Utilization by Node**: query per node, `1 - avg(rate(node_cpu_seconds_total{mode="idle", node="$node"}[5m])) by (node)`.
- **Memory Utilization by Node**: `(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)` by node.
- **Disk I/O by Node**: `rate(node_disk_read_bytes_total[5m])` and `rate(node_disk_written_bytes_total[5m])` stacked.

**Row 3 — Pod Resources (2 panels):**
- **Pod CPU Usage vs Request**: `sum(rate(container_cpu_usage_seconds_total{namespace="$namespace"}[5m])) by (pod)` overlaid with `kube_pod_container_resource_requests{resource="cpu"}`. Shows over/under-provisioning.
- **Pod Memory Usage vs Limit**: `sum(container_memory_working_set_bytes{namespace="$namespace"}) by (pod)` with `kube_pod_container_resource_limits{resource="memory"}` as threshold line.

**Row 4 — Saturation (2 panels):**
- **CPU Throttling**: `sum(rate(container_cpu_cfs_throttled_periods_total[5m])) / sum(rate(container_cpu_cfs_periods_total[5m])) by (pod)`. Threshold at 25%.
- **Pod Restart Rate**: `sum(increase(kube_pod_container_status_restarts_total{namespace="$namespace"}[1h])) by (pod)`. Table sorted desc.

**Row 5 — Database (2 panels):**
- **PostgreSQL Active Connections**: `pg_stat_activity_count{state="active"}`. Max connection threshold line.
- **PostgreSQL Query Duration P95**: `histogram_quantile(0.95, sum(rate(pg_stat_statements_seconds_bucket[5m])) by (le))`.

### Provisioning (`grafana/provisioning/dashboards.yaml`)

```yaml
apiVersion: 1
providers:
  - name: "Platform Dashboards"
    orgId: 1
    folder: "Platform"
    type: file
    disableDeletion: true
    editable: false
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: false
```

### Datasources (`grafana/provisioning/datasources.yaml`)

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus.monitoring:9090
    isDefault: true
    jsonData:
      timeInterval: "15s"
      httpMethod: POST
  - name: PostgreSQL
    type: postgres
    access: proxy
    url: postgres-metrics.database:5432
    database: metrics
    user: grafana_reader
    secureJsonData:
      password: "$POSTGRES_PASSWORD"
    jsonData:
      sslmode: require
      maxOpenConns: 10
      postgresVersion: 1600
```

### Expected Functionality

- Executive dashboard shows green/yellow/red indicators for platform health at a glance.
- Selecting service `checkout` in RED dashboard → shows checkout-specific request rate, error breakdown by route, latency heatmap, and upstream dependency calls.
- Infrastructure dashboard highlights a node with 92% CPU → orange threshold on node CPU panel.
- Pod memory usage exceeding limit → red threshold line breach visible on Pod Memory panel.
- Template variables allow drilling from cluster-wide to namespace to individual service/node.

## Acceptance Criteria

- Executive dashboard has stat panels for RPS, error rate, P95 latency, and active users with color-coded thresholds.
- SLO compliance bar gauge shows per-service availability percentage with min 95-100 range.
- Service RED dashboard implements Rate (by status code and route), Errors (timeseries + table), Duration (heatmap + percentiles + slow routes) panels.
- Infrastructure USE dashboard implements Utilization (CPU, memory, disk I/O), Saturation (CPU throttling, pod restarts), Errors per resource.
- All dashboards use template variables for filtering by environment, namespace, service, and node.
- Latency heatmap panel uses histogram bucket queries with spectral color scheme.
- Table panels rank routes/pods by metrics in descending order.
- Provisioning configs enable file-based dashboard and datasource management.
- PostgreSQL datasource uses SSL and restricted `grafana_reader` user.
