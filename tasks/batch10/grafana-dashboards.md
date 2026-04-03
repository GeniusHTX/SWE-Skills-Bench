# Task: Create a Service Health Grafana Dashboard with RED Method Panels and Threshold Alerts

## Background

The `grafana/grafana` repository contains frontend TypeScript source and backend Go source for the Grafana observability platform. A new dashboard JSON provisioning file is needed for monitoring a web API service using the RED method (Rate, Errors, Duration), along with a companion Go handler that validates and imports dashboard JSON via the Grafana HTTP API, and unit tests for the validation logic.

## Files to Create/Modify

- `public/app/features/dashboard/state/service-health-dashboard.json` (create) — Grafana dashboard JSON (schema version 36) implementing a complete RED + saturation monitoring dashboard for a generic HTTP API service
- `pkg/services/dashboards/service_health_validator.go` (create) — Go function `ValidateServiceHealthDashboard(raw []byte) error` that checks required panels, template variables, and alerting rules exist in a dashboard JSON before import
- `pkg/services/dashboards/service_health_validator_test.go` (create) — Table-driven unit tests for `ValidateServiceHealthDashboard` covering valid dashboards, missing panels, and malformed JSON

## Requirements

### Dashboard JSON Structure

- Dashboard title must be `"Service Health (RED)"` and must include tags `["red-method", "api", "service"]`
- Template variables required: `datasource` (type `datasource`, query `prometheus`) and `service` (type `query`, definition `label_values(http_requests_total, service)`)
- The `refresh` field must be set to `"30s"`
- Panels required and must appear in this order by `gridPos.y`:
  1. **Request Rate** — type `timeseries`, query `sum(rate(http_requests_total{service="$service"}[5m]))`, unit `reqps`
  2. **Error Rate %** — type `timeseries`, query `(sum(rate(http_requests_total{service="$service", status=~"5.."}[5m])) / sum(rate(http_requests_total{service="$service"}[5m]))) * 100`, unit `percent`, alert threshold at value `1` (severity `warning`) and `5` (severity `critical`)
  3. **P95 Latency** — type `timeseries`, query `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service="$service"}[5m])) by (le))`, unit `s`
  4. **P99 Latency** — type `timeseries`, same as P95 but quantile `0.99`
  5. **Active Connections** — type `stat`, query `sum(http_active_connections{service="$service"})`, unit `short`
- Each panel must reference `${datasource}` as its datasource uid

### Alert Rules in Dashboard

- The **Error Rate %** panel must embed a Grafana alert rule with `for: 5m`, condition `gt 1` for warning and `gt 5` for critical
- Alert annotations must include `summary` and `description` fields with `$service` templated in the message

### Validator Logic

- `ValidateServiceHealthDashboard` must return `nil` for any dashboard JSON that satisfies all structural requirements above
- Must return a descriptive error if the `datasource` template variable is missing
- Must return a descriptive error if the `service` template variable is missing
- Must return a descriptive error if any of the five required panel titles is absent (case-sensitive match against `"Request Rate"`, `"Error Rate %"`, `"P95 Latency"`, `"P99 Latency"`, `"Active Connections"`)
- Must return `json.SyntaxError` wrapped error for malformed JSON input
- Must not reject dashboards that have extra panels beyond the five required ones

### Expected Functionality

- Valid dashboard JSON with all five panels and both template variables → `ValidateServiceHealthDashboard` returns `nil`
- Dashboard missing the `service` variable → error message contains `"template variable"` and `"service"`
- Dashboard with `"P95 Latency"` panel renamed to `"p95 latency"` → error message contains `"P95 Latency"` (case-sensitive)
- Dashboard with six panels (five required + one extra) → validator returns `nil`
- Passing `[]byte("not json")` → returns a non-nil error wrapping `json.SyntaxError`

## Acceptance Criteria

- `public/app/features/dashboard/state/service-health-dashboard.json` is valid JSON parseable by `json.Unmarshal` and passes `ValidateServiceHealthDashboard` with no errors
- `ValidateServiceHealthDashboard` returns `nil` for the provided dashboard file and returns non-nil errors with descriptive messages for each missing required element
- Table-driven tests in `service_health_validator_test.go` cover: valid dashboard, missing `datasource` variable, missing `service` variable, each of the five missing panel titles individually, and malformed JSON input
- `go build ./pkg/services/dashboards/...` exits with code 0
- `go test ./pkg/services/dashboards/...` passes all test cases
