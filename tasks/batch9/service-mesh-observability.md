# Task: Implement a Service Mesh Observability Dashboard Generator for Linkerd

## Background

Linkerd (https://github.com/linkerd/linkerd2) provides built-in observability for service meshes. A new Go package in the `viz` module is needed that generates Grafana dashboard JSON models for Linkerd service mesh metrics: golden signals dashboards (latency, traffic, errors, saturation), service dependency maps, per-route metrics panels, and SLO tracking dashboards with error budget burn rate visualization.

## Files to Create/Modify

- `viz/pkg/dashboards/golden_signals.go` (create) — Generates a Grafana dashboard JSON with panels for the four golden signals: request rate, error rate, P50/P99 latency, and TCP connection saturation for a given service
- `viz/pkg/dashboards/dependency_map.go` (create) — Generates a Grafana dashboard with a node graph panel showing service-to-service dependencies, request rates on edges, and error rates as color indicators
- `viz/pkg/dashboards/route_metrics.go` (create) — Generates per-route metrics dashboard with latency histograms and success rates for each ServiceProfile route
- `viz/pkg/dashboards/slo_tracker.go` (create) — Generates an SLO tracking dashboard with error budget remaining, burn rate alerts (1h, 6h, 3d windows), and compliance timeline
- `viz/pkg/dashboards/types.go` (create) — Shared Grafana dashboard model types: Dashboard, Panel, Target (PromQL query), GridPos, Threshold, Variable
- `viz/pkg/dashboards/dashboards_test.go` (create) — Unit tests for all dashboard generators

## Requirements

### Types (`types.go`)

- `Dashboard` struct: `Title`, `UID`, `Tags []string`, `Panels []Panel`, `Templating TemplatingConfig`, `Time TimeRange`, `Refresh string`
- `Panel` struct: `ID int`, `Title string`, `Type string` (graph, stat, gauge, table, nodeGraph, timeseries), `GridPos GridPos`, `Targets []Target`, `Thresholds []Threshold`, `Unit string`, `Description string`
- `Target` struct: `Expr string` (PromQL), `LegendFormat string`, `RefID string`, `Interval string`
- `GridPos` struct: `H, W, X, Y int` (Grafana grid layout)
- `Threshold` struct: `Value float64`, `Color string`, `Op string` (gt/lt)
- `TemplatingConfig` struct: `List []Variable`
- `Variable` struct: `Name`, `Label`, `Type string` (query/custom/constant), `Query string`, `Current string`
- Method `Dashboard.ToJSON() ([]byte, error)` — Marshals the dashboard to Grafana-compatible JSON
- All dashboard UIDs must be deterministic (derived from service name and dashboard type)

### Golden Signals Dashboard (`golden_signals.go`)

- Function `GenerateGoldenSignals(service, namespace string) Dashboard`:
- Template variables: `$namespace` (query: `label_values(namespace)`), `$interval` (custom: `1m,5m,15m`)
- Panel 1 — "Request Rate" (timeseries):
  - PromQL: `sum(rate(response_total{namespace="$namespace", deployment="<service>"}[$interval]))`
  - Unit: `reqps`
- Panel 2 — "Error Rate %" (timeseries + stat):
  - PromQL: `sum(rate(response_total{namespace="$namespace", deployment="<service>", classification="failure"}[$interval])) / sum(rate(response_total{namespace="$namespace", deployment="<service>"}[$interval])) * 100`
  - Thresholds: green < 1%, yellow < 5%, red >= 5%
  - Unit: `percent`
- Panel 3 — "Latency P50 / P99" (timeseries, two targets):
  - P50: `histogram_quantile(0.50, sum(rate(response_latency_ms_bucket{namespace="$namespace", deployment="<service>"}[$interval])) by (le))`
  - P99: same with `0.99`
  - Unit: `ms`
- Panel 4 — "TCP Connections" (timeseries):
  - PromQL: `sum(tcp_open_connections{namespace="$namespace", deployment="<service>"})`
  - Unit: `short`
- Layout: 4 panels in a 2x2 grid, each 12x8 Grafana units

### Dependency Map Dashboard (`dependency_map.go`)

- Function `GenerateDependencyMap(namespace string) Dashboard`:
- Panel 1 — "Service Dependency Graph" (nodeGraph type):
  - Node query: `sum by (deployment) (rate(response_total{namespace="$namespace"}[$interval]))`
  - Edge query: `sum by (deployment, dst_deployment) (rate(response_total{namespace="$namespace"}[$interval]))`
  - Edge color based on error rate: green (<1%), yellow (1-5%), red (>5%)
- Panel 2 — "Top Error Routes" (table):
  - PromQL: `topk(10, sum by (deployment, route) (rate(response_total{namespace="$namespace", classification="failure"}[$interval])))`
- Panel 3 — "Cross-Service Latency" (heatmap):
  - PromQL: `sum by (le, dst_deployment) (rate(response_latency_ms_bucket{namespace="$namespace"}[$interval]))`

### Route Metrics Dashboard (`route_metrics.go`)

- Function `GenerateRouteMetrics(service, namespace string) Dashboard`:
- Repeating variable `$route` populated by: `label_values(route_response_total{namespace="$namespace", deployment="<service>"}, route)`
- Per-route panels (repeated):
  - "Route Success Rate" (gauge): `1 - (rate(route_response_total{..., classification="failure", route="$route"}[$interval]) / rate(route_response_total{..., route="$route"}[$interval]))`
  - "Route Latency Distribution" (histogram): `sum(rate(route_response_latency_ms_bucket{..., route="$route"}[$interval])) by (le)`
  - "Route Request Rate" (stat): `sum(rate(route_response_total{..., route="$route"}[$interval]))`

### SLO Tracker Dashboard (`slo_tracker.go`)

- Function `GenerateSLOTracker(service, namespace string, sloTarget float64) Dashboard`:
- `sloTarget` is the availability SLO (e.g., 0.999 for 99.9%)
- Panel 1 — "Error Budget Remaining" (gauge):
  - Formula: `1 - ((1 - success_rate_28d) / (1 - sloTarget))`
  - Thresholds: green > 50%, yellow > 25%, red <= 25%
  - Unit: `percentunit`
- Panel 2 — "Burn Rate (Multi-Window)" (timeseries, 3 targets):
  - 1h burn rate: `error_rate_1h / (1 - sloTarget)`
  - 6h burn rate: `error_rate_6h / (1 - sloTarget)`
  - 3d burn rate: `error_rate_3d / (1 - sloTarget)`
  - Alert threshold at burn rate = 1.0 (error budget consumed at normal rate)
- Panel 3 — "SLO Compliance Timeline" (timeseries):
  - 28d rolling availability vs SLO target line
- Panel 4 — "Monthly Error Budget Consumption" (bar gauge):
  - Shows daily error budget consumption over past 30 days

### Expected Functionality

- Golden signals dashboard for service "web" in namespace "default" produces 4 panels with correct PromQL queries referencing "web"
- Dependency map node graph includes both node and edge queries for service topology
- SLO tracker with target 0.999 calculates error budget as `(1 - success_rate) / 0.001` and burn rate threshold at 1.0
- All dashboards produce valid JSON parseable by `json.Unmarshal`

## Acceptance Criteria

- Golden signals panels cover all 4 signals with correct PromQL and Linkerd metric names
- Dashboard UIDs are deterministic and unique per service/dashboard-type
- Template variables use `label_values()` for dynamic namespace and route selection
- SLO error budget formula correctly uses the target to calculate remaining budget percentage
- Burn rate uses multi-window approach (1h, 6h, 3d) with threshold at 1.0
- All panel thresholds have appropriate color coding (green/yellow/red)
- `go build ./viz/...` compiles successfully
- `python -m pytest /workspace/tests/test_service_mesh_observability.py -v --tb=short` passes
