# Task: Instrument Linkerd2 Visibility Layer with Golden Signal Metrics and Dashboards

## Background

The `linkerd/linkerd2` repository contains a `viz` component (`viz/`) that provides observability features for the service mesh. The current implementation needs extended observability coverage: Prometheus recording rules for the four golden signals, a complete Grafana dashboard JSON definition, and new Go metric collectors integrated into the existing viz metrics server.

## Files to Create/Modify

- `viz/metrics-api/prometheus.go` (modify) — Add new PromQL query functions for golden signal metrics (latency P50/P95/P99, error rate, request rate, saturation)
- `viz/metrics-api/gen/viz.pb.go` — Do not modify generated file; update source proto instead
- `viz/charts/prometheus/templates/prometheus-configmap.yaml` (modify) — Add recording rules groups for `linkerd_golden_signals`
- `viz/charts/grafana/dashboards/linkerd-service-health.json` (create) — Grafana dashboard JSON with panels following the RED method
- `viz/metrics-api/prometheus_test.go` (modify) — Add unit tests for new query functions covering edge cases

## Requirements

### Recording Rules

- Add a Prometheus recording rules group named `linkerd_golden_signals` to `viz/charts/prometheus/templates/prometheus-configmap.yaml`
- The group must define four rules using `linkerd_tcp_open_connections`, `linkerd_request_total`, `linkerd_response_latency_ms_bucket`, and `linkerd_response_total` metrics
- Recording rule names must follow the pattern `job:linkerd_<signal>:rate5m`
- Latency rules must produce P50, P95, and P99 quantiles using `histogram_quantile` over a 5-minute window
- Error rate rule must compute the ratio of `classification="failure"` responses to total responses

### Grafana Dashboard

- Create `viz/charts/grafana/dashboards/linkerd-service-health.json` as a valid Grafana dashboard JSON (schema version 36)
- The dashboard must include a `service` template variable that populates from `label_values(linkerd_request_total, dst_service)`
- Panels required: request rate (time series), error rate % (time series with alert threshold at 1%), P99 latency in ms (time series), active TCP connections (stat panel)
- All panel queries must reference the recording rules defined in the configmap (not raw metrics) except where recording rules are not applicable
- Each panel must set `datasource` to `${datasource}` using a dashboard-level datasource variable

### Metrics API

- In `viz/metrics-api/prometheus.go`, add functions `GoldenSignalQueries(service, namespace string) map[string]string` returning the four PromQL expressions keyed by `"request_rate"`, `"error_rate"`, `"latency_p99"`, `"tcp_connections"`
- When `service` is empty, queries must aggregate across all services in the given `namespace`
- When both `service` and `namespace` are empty, queries must aggregate cluster-wide

### Expected Functionality

- `GoldenSignalQueries("web", "production")` → returns four queries with label selectors `dst_service="web", namespace="production"`
- `GoldenSignalQueries("", "staging")` → returns queries scoped to `namespace="staging"` without a service filter
- `GoldenSignalQueries("", "")` → returns cluster-wide queries with no label selectors
- Invalid service name containing characters outside `[a-z0-9-.]` → function returns an error before constructing queries
- Dashboard JSON parses without errors when loaded by Grafana provisioning; all panel targets reference valid recording rule names

## Acceptance Criteria

- `viz/charts/prometheus/templates/prometheus-configmap.yaml` contains a `linkerd_golden_signals` recording rules group with exactly four rules covering request rate, error rate, P50/P95/P99 latency, and TCP connections
- `viz/charts/grafana/dashboards/linkerd-service-health.json` is valid JSON, contains a `service` template variable, and at least four panels covering the RED signals plus TCP connections
- `GoldenSignalQueries` returns non-empty strings for all four keys under valid inputs and returns an error for invalid service names
- Unit tests in `viz/metrics-api/prometheus_test.go` cover the empty-service, empty-namespace, and invalid-name cases
- `go build ./viz/...` exits with code 0 after all changes
