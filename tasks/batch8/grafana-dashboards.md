# Task: Create a Provisioned Service Health Dashboard with RED Method Panels

## Background

Grafana supports provisioned dashboards that can be stored as JSON files and loaded automatically. A new service health dashboard is needed that follows the RED method (Rate, Errors, Duration) to monitor HTTP service performance. The dashboard must be defined as a valid Grafana dashboard JSON model and accompanied by a Go utility that generates the JSON programmatically from a service configuration file.

## Files to Create/Modify

- `devenv/dashboards/service-health/service-health-red.json` (new) — Provisioned Grafana dashboard JSON showing RED method panels for a configurable HTTP service
- `pkg/dashboards/redgenerator/generator.go` (new) — Go utility that reads a YAML service config and generates the service health dashboard JSON
- `pkg/dashboards/redgenerator/generator_test.go` (new) — Unit tests for the dashboard generator
- `pkg/dashboards/redgenerator/types.go` (new) — Type definitions for service config input and dashboard JSON model
- `devenv/dashboards/service-health/service-config.yaml` (new) — Example YAML configuration for a sample HTTP service

## Requirements

### Dashboard JSON Structure

- The dashboard must have `uid` set to `service-health-red`, `title` set to "Service Health — RED Method", and `schemaVersion` of at least 39
- Template variables: `$service` (query type, sourced from `label_values(http_requests_total, service)`), `$interval` (interval type, values: 1m, 5m, 15m, 1h)
- Time range default: last 1 hour with auto-refresh every 30 seconds
- The dashboard must contain exactly 6 panels arranged in a 2×3 grid (2 columns, 3 rows) using `gridPos`

### Panel Definitions

- **Row 1 — Rate**: Panel 1 is a time series showing `rate(http_requests_total{service="$service"}[$interval])` with legend `{{method}} {{status_code}}`; Panel 2 is a stat panel showing the current total request rate as a single number
- **Row 2 — Errors**: Panel 3 is a time series showing the error ratio `rate(http_requests_total{service="$service", status_code=~"5.."}[$interval]) / rate(http_requests_total{service="$service"}[$interval])`; Panel 4 is a gauge panel showing the current error percentage with thresholds (green < 1%, yellow < 5%, red >= 5%)
- **Row 3 — Duration**: Panel 5 is a time series showing `histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{service="$service"}[$interval]))` and the 0.95 and 0.99 quantiles as separate series; Panel 6 is a heatmap panel based on `http_request_duration_seconds_bucket`
- All panels must use Prometheus as the datasource with uid `"${DS_PROMETHEUS}"`
- Each panel must have a unique numeric `id`, a descriptive `title`, and valid `gridPos` with `h`, `w`, `x`, `y` fields

### Dashboard Generator

- The generator reads a YAML config specifying: `service_name`, `datasource_uid`, `metrics_prefix` (default: `http`), `quantiles` (list, default: [0.5, 0.95, 0.99]), `error_code_pattern` (default: `5..`), `grid_width` (default: 12 per column)
- Output is a complete, valid Grafana dashboard JSON written to stdout or a specified file path
- If `service_name` is empty, the generator returns an error
- If `quantiles` list is empty, the generator falls back to the default `[0.5, 0.95, 0.99]`
- Panel IDs are auto-generated starting from 1

### Service Config YAML

- The example config defines a service named `checkout-api` with datasource uid `prometheus-main`, metrics prefix `http`, quantiles `[0.5, 0.95, 0.99]`, and error code pattern `5..`

### Expected Functionality

- Loading `service-health-red.json` into Grafana renders 6 panels in a 2×3 grid with correct Prometheus queries
- Running the generator with the example YAML config produces JSON that is structurally identical to the handcrafted dashboard file (same panels, queries, thresholds, gridPos layout)
- Running the generator with an empty `service_name` returns a clear validation error
- Running the generator with custom quantiles `[0.5, 0.75, 0.99]` produces a duration time series panel with three series instead of the default three
- The generated JSON passes `jq .` validation (valid JSON) and contains all required Grafana dashboard fields (`uid`, `title`, `schemaVersion`, `panels`, `templating`)

## Acceptance Criteria

- The provisioned dashboard JSON is valid, loadable by Grafana, and contains exactly 6 panels arranged in the specified 2×3 grid layout
- Rate, Error, and Duration panels use the correct Prometheus queries with template variable substitution
- The error gauge panel has thresholds at 1% (yellow) and 5% (red)
- The duration panel displays P50, P95, and P99 latency series
- The Go generator produces equivalent dashboard JSON from the YAML config input
- Generator validates input and returns errors for missing `service_name`
- Unit tests verify panel count, query correctness, threshold values, gridPos layout, and error cases
