# Task: Create Grafana Dashboard Provisioning for a Microservice Monitoring Stack

## Background

Grafana (https://github.com/grafana/grafana) is an open-source monitoring and observability platform. The project needs a provisioned dashboard configuration for monitoring a microservice application stack, demonstrating RED (Rate, Errors, Duration) and USE (Utilization, Saturation, Errors) method panels, template variables, alerting rules, and dashboard-as-code provisioning.

## Files to Create/Modify

- `devenv/dashboards/microservice-monitoring.json` (create) — Grafana dashboard JSON model with RED/USE panels
- `devenv/dashboards/provisioning.yaml` (create) — Dashboard provisioning configuration
- `devenv/alerting/alert-rules.yaml` (create) — Alerting rules for the dashboard panels
- `devenv/dashboards/panels/red-panels.json` (create) — Reusable RED method panel definitions
- `devenv/dashboards/panels/use-panels.json` (create) — Reusable USE method panel definitions

## Requirements

### Dashboard Structure

- Dashboard title: "Microservice Monitoring"
- Time range: last 1 hour (default), with refresh interval of 30 seconds
- Template variables:
  - `$namespace` — Kubernetes namespace selector, query type sourced from Prometheus label values of `namespace` on `up` metric
  - `$service` — Service selector, filtered by `$namespace`, sourced from `job` label values
  - `$interval` — Interval variable with values: `1m`, `5m`, `15m`, `1h`
- Dashboard tags: `["monitoring", "microservices", "sre"]`
- Dashboard UID: `microservice-monitoring-v1` (for stable provisioning references)

### RED Method Panels (Rate, Errors, Duration)

- **Request Rate** panel: Stat panel showing `sum(rate(http_requests_total{namespace="$namespace", job="$service"}[$interval]))` with unit `reqps`, thresholds at 100 (green), 1000 (yellow), 5000 (red)
- **Error Rate** panel: Gauge panel showing `sum(rate(http_requests_total{status=~"5.."}[$interval])) / sum(rate(http_requests_total[$interval])) * 100` with unit `percent`, thresholds at 1% (green), 5% (yellow), 10% (red)
- **Request Duration** panel: Time series graph showing p50, p90, p99 latencies using `histogram_quantile(0.5, rate(http_request_duration_seconds_bucket[$interval]))`, etc., with unit `s`, legend format `{{quantile}}`
- **Error Rate Over Time** panel: Time series graph showing error rate trend with a fixed threshold line at 5%

### USE Method Panels (Utilization, Saturation, Errors)

- **CPU Utilization** panel: Time series showing `rate(container_cpu_usage_seconds_total{namespace="$namespace", pod=~"$service.*"}[$interval])` vs `kube_pod_container_resource_limits{resource="cpu"}`, unit `percentunit`
- **Memory Utilization** panel: Time series showing `container_memory_working_set_bytes / kube_pod_container_resource_limits{resource="memory"}`, unit `percentunit`
- **CPU Saturation** panel: Stat panel showing throttled seconds `rate(container_cpu_cfs_throttled_seconds_total[$interval])`, thresholds at 0.1 (green), 1 (yellow), 5 (red)
- **Pod Restarts** panel: Stat panel showing `increase(kube_pod_container_status_restarts_total[$interval])`, thresholds at 0 (green), 1 (yellow), 5 (red)

### Dashboard Layout

- Organize panels in rows:
  - Row 1: "RED — Traffic Overview" with Request Rate, Error Rate, Error Rate Over Time
  - Row 2: "RED — Latency" with Request Duration (full width)
  - Row 3: "USE — Resources" with CPU Utilization, Memory Utilization, CPU Saturation, Pod Restarts
- Each panel has `gridPos` specifying position in the 24-column Grafana grid
- Rows are collapsible

### Alerting Rules

- Define alert rules in YAML provisioning format:
  - `HighErrorRate`: fires when error rate > 5% for 5 minutes; severity `critical`; annotation with `summary` and `description` using `{{ $value }}`
  - `HighLatency`: fires when p99 latency > 2s for 10 minutes; severity `warning`
  - `HighPodRestarts`: fires when pod restarts > 3 in 15 minutes; severity `warning`
- Each alert references the dashboard UID and panel ID for linking
- Configure notification channel: `default` contact point

### Provisioning Configuration

- Provisioning YAML configures Grafana to auto-load dashboards from the `devenv/dashboards/` directory
- Set `updateIntervalSeconds: 30` for auto-refresh
- Set `allowUiUpdates: false` to prevent manual changes overriding provisioned content
- Set the folder to "Microservices" in Grafana's dashboard structure

### Expected Functionality

- Importing `microservice-monitoring.json` into Grafana renders all panels with correct PromQL queries
- Selecting a different `$namespace` value updates all panels
- The latency panel shows 3 lines (p50, p90, p99) with correct legend labels
- Error rate gauge shows percentage with correct threshold colors
- Alerting rules evaluate correctly and fire when thresholds are breached
- Provisioning YAML auto-loads the dashboard on Grafana startup

## Acceptance Criteria

- Dashboard JSON is valid and importable into Grafana (version 10+)
- All template variables are defined with correct query types and datasource references
- RED panels use correct PromQL queries with template variable substitution
- USE panels reference correct container and Kubernetes metrics
- Panel layout uses the 24-column grid with correct `gridPos` positioning
- Rows are collapsible and properly group related panels
- Alert rules reference correct metrics, thresholds, and durations with proper annotations
- Provisioning YAML correctly configures auto-loading with the specified folder and update interval
- Reusable panel definitions in separate JSON files can be referenced by the main dashboard
