# Task: Build a Grafana Dashboard JSON Generator for Application Monitoring

## Background

Grafana (https://github.com/grafana/grafana) provides visualization for metrics. A new Go package is needed that generates production-ready Grafana dashboard JSON models programmatically, supporting RED method dashboards (Rate, Errors, Duration), USE method infrastructure dashboards (Utilization, Saturation, Errors), business KPI dashboards with stat panels, and a dashboard-as-code pattern with variable templating, annotations, and panel linking.

## Files to Create/Modify

- `pkg/dashboards/model.go` (create) — Complete Go types for Grafana dashboard JSON: Dashboard, Panel, Target, GridPos, Threshold, Variable, Annotation, Legend, FieldConfig, PanelLinks
- `pkg/dashboards/red_dashboard.go` (create) — `GenerateREDDashboard(service string) Dashboard` — creates a RED method dashboard for an HTTP service with request rate, error rate, and latency panels
- `pkg/dashboards/use_dashboard.go` (create) — `GenerateUSEDashboard(node string) Dashboard` — creates a USE method dashboard for infrastructure monitoring with CPU, memory, disk, and network panels
- `pkg/dashboards/business_dashboard.go` (create) — `GenerateBusinessDashboard(metrics []BusinessMetric) Dashboard` — creates a KPI dashboard with stat, gauge, and bar chart panels
- `pkg/dashboards/variables.go` (create) — Template variable generators: datasource, query-based, custom, interval, text box, and constant variables
- `pkg/dashboards/alerts.go` (create) — Grafana unified alerting rule generators: alert rule YAML for `alerting` provisioning directory
- `pkg/dashboards/provisioning.go` (create) — Dashboard provisioning file generator for `dashboards.yaml`
- `pkg/dashboards/builder.go` (create) — `DashboardBuilder` fluent API for composing dashboards
- `pkg/dashboards/model_test.go` (create) — Tests for JSON serialization and dashboard structure

## Requirements

### Model (`model.go`)

- `Dashboard` struct with all standard Grafana fields:
  - `Title`, `UID`, `Tags []string`, `Timezone string` (browser/utc), `Refresh string`, `SchemaVersion int` (38)
  - `Panels []Panel`, `Templating Templating`, `Annotations AnnotationList`, `Links []DashboardLink`
  - `Time TimeRange` (`{"from": "now-1h", "to": "now"}`), `Timepicker Timepicker`
- `Panel` struct: `ID int`, `Title`, `Type string`, `GridPos GridPos`, `Targets []Target`
  - `FieldConfig FieldConfig`, `Options PanelOptions`, `Transformations []Transformation`
  - `Alert *AlertConfig`, `Links []PanelLink`, `Description string`
- `FieldConfig` struct: `Defaults FieldConfigDefaults`, `Overrides []FieldOverride`
- `FieldConfigDefaults`: `Unit`, `Thresholds ThresholdsConfig`, `Color ColorConfig`, `Min, Max *float64`, `Mappings []ValueMapping`
- `ThresholdsConfig`: `Mode string` (absolute/percentage), `Steps []ThresholdStep`
- Method `Dashboard.ToJSON() ([]byte, error)` — Marshal with `json.MarshalIndent`

### RED Dashboard (`red_dashboard.go`)

- Function `GenerateREDDashboard(service, namespace string, datasource string) Dashboard`:
- Required variables: `$datasource` (datasource type), `$namespace` (query), `$interval` (custom: `1m,5m,15m,30m,1h`)
- Panel layout in rows (each row 8 units tall):
  - **Row 1: Rate**
    - "Request Rate" (timeseries, W=24): `sum(rate(http_requests_total{service="<service>", namespace="$namespace"}[$interval])) by (method)`, unit=`reqps`
  - **Row 2: Errors**
    - "Error Rate %" (timeseries, W=12): `sum(rate(http_requests_total{...status=~"5.."}[$interval])) / sum(rate(http_requests_total{...}[$interval])) * 100`, unit=`percent`
    - Threshold: green < 1, yellow < 5, red >= 5
    - "Total Errors" (stat, W=12): `sum(increase(http_requests_total{...status=~"5.."}[$interval]))`
  - **Row 3: Duration**
    - "P50 Latency" (timeseries, W=8): histogram_quantile 0.5, unit=`ms`
    - "P95 Latency" (timeseries, W=8): histogram_quantile 0.95, unit=`ms`
    - "P99 Latency" (timeseries, W=8): histogram_quantile 0.99, unit=`ms`
  - **Row 4: Summary**
    - "Availability" (gauge, W=8): 1 - error_rate, unit=`percentunit`, thresholds: green>99.9%, yellow>99%, red<99%
    - "Req/s (current)" (stat, W=8): current request rate
    - "Active Connections" (stat, W=8): `http_connections_active{...}` if available

### USE Dashboard (`use_dashboard.go`)

- Function `GenerateUSEDashboard(job, instance string, datasource string) Dashboard`:
- Panels:
  - "CPU Utilization" (timeseries): `1 - avg(rate(node_cpu_seconds_total{mode="idle",job="$job"}[5m]))`, unit=`percentunit`
  - "CPU Saturation" (timeseries): `node_load1{job="$job"} / count(node_cpu_seconds_total{mode="idle",job="$job"})`, unit=`short`
  - "Memory Utilization" (timeseries): `1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)`, unit=`percentunit`
  - "Memory Used" (stat): bytes used, unit=`bytes`
  - "Disk I/O Utilization" (timeseries): `rate(node_disk_io_time_seconds_total{job="$job"}[5m])`, unit=`percentunit`
  - "Disk Space" (gauge): `1 - node_filesystem_avail_bytes / node_filesystem_size_bytes`, unit=`percentunit`
  - "Network Receive Rate" (timeseries): `rate(node_network_receive_bytes_total{job="$job"}[5m])`, unit=`Bps`
  - "Network Transmit Rate" (timeseries): same for transmit, unit=`Bps`

### Business Dashboard (`business_dashboard.go`)

- Struct `BusinessMetric`: `Name string`, `Expr string`, `Unit string`, `TargetValue *float64`, `PanelType string`
- Function `GenerateBusinessDashboard(title string, metrics []BusinessMetric, datasource string) Dashboard`:
  - Each metric becomes a panel (stat or gauge based on PanelType)
  - If `TargetValue` is set: add threshold at target (green above, yellow -10%, red -20%)
  - Arrange in a responsive grid: 4 panels per row, 6 wide each (total 24)
  - Add a "Trends" row at the bottom with all metrics as timeseries overlaid

### Variables (`variables.go`)

- Function `DataSourceVariable(name, label, pluginID string) Variable`:
  - Type: `datasource`, `pluginId` from argument
- Function `QueryVariable(name, label, query, datasource, refresh string) Variable`:
  - Type: `query`, `definition`, `refresh` (1=on_dashboard_load, 2=on_time_range_change)
  - `sort: 1` (alphabetical)
- Function `IntervalVariable(name string, intervals []string, auto bool) Variable`:
  - Type: `interval`, `auto: auto`, `auto_count: 30`, `auto_min: "10s"`
- Function `CustomVariable(name, label string, values []string) Variable`:
  - Type: `custom`, options array from values

### Alerting Rules (`alerts.go`)

- Function `GenerateHighErrorRateAlert(service, namespace string, threshold float64) AlertRule`:
  - YAML structure for Grafana unified alerting
  - Condition: error rate > threshold for 5 minutes
  - Labels: `severity: "critical"`, `service: <service>`
  - Annotations: `summary` and `description` templates using `{{ $value }}`
- Function `GenerateHighLatencyAlert(service, namespace string, p99ThresholdMs float64) AlertRule`
- Method `ToAlertingYAML(rules []AlertRule) ([]byte, error)` — Generates provisioning YAML

### Provisioning (`provisioning.go`)

- Function `GenerateDashboardProvisioning(folders []ProvisionFolder) ([]byte, error)`:
  - Output: `dashboards.yaml` for Grafana provisioning
  - Each folder: `name`, `path`, `disableDeletion`, `updateIntervalSeconds`
  - `allowUiUpdates: false` for production
- Function `GenerateDatasourceProvisioning(sources []DatasourceConfig) ([]byte, error)`:
  - Output: `datasources.yaml` with Prometheus datasource at `http://prometheus:9090`

### Expected Functionality

- RED dashboard for service "api" in namespace "production" produces 8+ panels covering rate, error rate, P50/P95/P99 latency, and an availability gauge
- USE dashboard produces 8 resource panels covering CPU, memory, disk, and network
- Business dashboard with 6 metrics generates 6 stat panels in 2 rows, plus a trends timeseries row
- Alert rules serialize to valid Grafana unified alerting YAML with proper condition syntax

## Acceptance Criteria

- All generated dashboards have `schemaVersion: 38` and a deterministic `uid`
- RED dashboard panels cover all three signals with correct PromQL
- Error rate panel has green/yellow/red thresholds at 1%/5%
- USE dashboard covers utilization, saturation, and error signals for all 4 resource types
- Template variables include datasource and interval selectors
- Alerting YAML validates against Grafana's unified alerting schema
- Provisioning YAML enables `disableDeletion: true` for production safety
- All JSON output is parseable and valid
- `python -m pytest /workspace/tests/test_grafana_dashboards.py -v --tb=short` passes
