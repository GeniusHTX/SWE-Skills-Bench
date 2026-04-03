# Task: Build Linkerd Service Mesh Observability Dashboards and Metrics Export

## Background

Linkerd (https://github.com/linkerd/linkerd2) includes a `viz` extension for observability. This task requires creating a Go-based metrics aggregation service that reads Linkerd's Prometheus metrics, computes golden signal summaries per service, and exposes a REST API for service health dashboards. The service integrates with Linkerd's existing `viz/` package structure.

## Files to Create/Modify

- `viz/metrics/aggregator.go` (create) — `MetricsAggregator` struct that queries Prometheus for Linkerd proxy metrics (`request_total`, `response_total`, `response_latency_ms_bucket`) and computes per-service golden signals: request rate, success rate, P50/P95/P99 latency.
- `viz/metrics/golden_signals.go` (create) — Data types: `GoldenSignals` struct with `RequestRate`, `SuccessRate`, `P50Latency`, `P95Latency`, `P99Latency`, `ErrorRate` fields. `ServiceHealth` struct embedding `GoldenSignals` with `ServiceName`, `Namespace`, `Status` (healthy/degraded/critical).
- `viz/metrics/health_checker.go` (create) — `HealthChecker` that evaluates `GoldenSignals` against configurable thresholds and assigns `Status`. Thresholds: `success_rate < 0.99` → degraded, `< 0.95` → critical; `p99_latency > 500ms` → degraded, `> 2000ms` → critical.
- `viz/metrics/api.go` (create) — HTTP handler exposing: `GET /api/services` (list all services with health), `GET /api/services/{name}` (detail with golden signals time series), `GET /api/topology` (service dependency graph from request metrics).
- `viz/metrics/topology.go` (create) — `TopologyBuilder` that constructs a service dependency graph from `response_total` metrics (using `dst_service` and `src_service` labels). Returns `edges` with caller, callee, request rate, and error rate.
- `viz/metrics/aggregator_test.go` (create) — Tests with mocked Prometheus responses for golden signal computation, health evaluation, and topology building.

## Requirements

### Metrics Aggregator

- `NewMetricsAggregator(prometheusURL string, queryTimeout time.Duration)`.
- `GetGoldenSignals(ctx, serviceName, namespace string, window time.Duration) (*GoldenSignals, error)` — executes PromQL queries:
  - Request rate: `sum(rate(response_total{deployment="{service}", namespace="{ns}"}[{window}]))`.
  - Success rate: `sum(rate(response_total{classification="success", ...}[{window}])) / sum(rate(response_total{...}[{window}]))`.
  - P50/P95/P99: `histogram_quantile(0.50/0.95/0.99, sum(rate(response_latency_ms_bucket{...}[{window}])) by (le))`.
- `GetAllServices(ctx, namespace string) ([]ServiceHealth, error)` — discovers services from `response_total` metric labels and computes golden signals for each.

### Health Checker

- `NewHealthChecker(config HealthConfig)`.
- `HealthConfig`: `SuccessRateDegraded` (default 0.99), `SuccessRateCritical` (0.95), `LatencyP99Degraded` (500ms), `LatencyP99Critical` (2000ms).
- `Evaluate(signals GoldenSignals) Status` — returns `healthy`, `degraded`, or `critical` based on worst-case metric.

### Topology Builder

- `BuildTopology(ctx, namespace string, window time.Duration) (*Topology, error)`.
- `Topology` has `Nodes []ServiceNode` and `Edges []ServiceEdge`.
- `ServiceEdge`: `Source`, `Destination`, `RequestRate`, `SuccessRate`.
- Deduplication: if both `A→B` and `B→A` edges exist, they are separate entries.

### API Endpoints

- `GET /api/services?namespace=default` → JSON array of `ServiceHealth` objects.
- `GET /api/services/order-service?namespace=default&window=5m` → JSON `ServiceHealth` with full golden signals.
- `GET /api/topology?namespace=default&window=5m` → JSON with `nodes` and `edges` arrays.
- All endpoints return proper HTTP error codes: 400 for invalid parameters, 502 for Prometheus query failures.

### Expected Functionality

- Service with 99.5% success rate → status `degraded`.
- Service with 100% success rate but P99 = 1200ms → status `degraded`.
- Service with 93% success rate → status `critical`.
- Topology for 3 services where A calls B and B calls C → 2 edges: `A→B`, `B→C`.

## Acceptance Criteria

- `MetricsAggregator` executes correct PromQL queries with parameterized service names and time windows.
- `GoldenSignals` correctly computes all 5 metrics from Prometheus responses.
- `HealthChecker` correctly evaluates health based on configurable thresholds.
- `TopologyBuilder` constructs a valid dependency graph from metric labels.
- API endpoints return correct JSON structures with proper error handling.
- Tests verify golden signal computation, health evaluation, topology building, and API response formatting.
- Code compiles with `go build ./viz/metrics/...`.
