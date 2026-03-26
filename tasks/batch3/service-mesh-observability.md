# Task: Build a Service Mesh Observability Dashboard Data Generator for Linkerd

## Background

Linkerd (https://github.com/linkerd/linkerd2) is a lightweight service mesh for Kubernetes. The `viz` extension provides observability features. The project needs a new component that collects golden signal metrics (latency, traffic, errors, saturation) from Linkerd's Prometheus metrics, computes per-service health scores, and generates structured data for dashboard consumption in the `viz/` package.

## Files to Create/Modify

- `viz/metrics/collector.go` (create) — Metrics collector that queries Prometheus for Linkerd-specific golden signal metrics
- `viz/metrics/health_scorer.go` (create) — Service health scoring engine based on golden signals and SLO targets
- `viz/metrics/topology.go` (create) — Service topology builder from observed traffic patterns
- `viz/metrics/collector_test.go` (create) — Tests for metrics collection
- `viz/metrics/health_scorer_test.go` (create) — Tests for health scoring

## Requirements

### Golden Signal Metrics Collection

- Implement a `MetricsCollector` struct that queries Prometheus for Linkerd proxy metrics:
  - **Latency**: `response_latency_ms_bucket` histogram — compute p50, p95, p99 per service and per route
  - **Traffic**: `request_total` counter — compute requests per second per service
  - **Errors**: `response_total{classification="failure"}` counter — compute error rate (errors / total) per service
  - **Saturation**: `tcp_open_connections` gauge — current connection count per service
- Accept a `PrometheusQuerier` interface: `Query(ctx context.Context, query string, ts time.Time) (model.Value, error)` — to allow testing with mock data
- Each metric query uses Linkerd's label conventions: `deployment`, `namespace`, `pod`, `authority` (destination), `direction` (inbound/outbound)
- Return a `ServiceMetrics` struct per service containing all four golden signals with their current values

### Service Health Scoring

- Implement a `HealthScorer` that computes a health score (0.0–1.0) per service based on:
  - Error rate vs. target: if error rate < 0.1%, score = 1.0; linear degradation to 0.0 at 5% error rate
  - p99 latency vs. target: if p99 < 200ms, score = 1.0; linear degradation to 0.0 at 2000ms
  - Traffic anomaly: if current RPS is < 10% of the 1-hour average, score penalty of 0.3 (potential outage)
- Overall health = weighted average: error_score (weight 0.5) + latency_score (weight 0.3) + traffic_score (weight 0.2)
- Classify overall health: `healthy` (≥ 0.8), `degraded` (0.5–0.79), `critical` (< 0.5)
- Configurable thresholds via a `HealthConfig` struct

### Service Topology

- Implement a `TopologyBuilder` that constructs a service dependency graph from Linkerd traffic metrics
- Each edge represents observed traffic between two services with: `source` (service name), `destination` (service name), `request_rate` (RPS), `error_rate`, `p99_latency_ms`
- Detect circular dependencies: if A → B → C → A exists, flag it in the topology output
- Identify gateway services (services with > 5 downstream dependencies) and leaf services (services with zero downstream dependencies)

### Output Format

- All output structs must implement JSON marshaling with `json` struct tags
- The topology output includes: `nodes` (list of services with health scores) and `edges` (list of traffic relationships)
- Include a `generated_at` timestamp in ISO 8601 format on all outputs

### Expected Functionality

- A service with 0.5% error rate has error_score = 1.0 − (0.005 / 0.05) = 0.9
- A service with p99 = 1000ms has latency_score = 1.0 − (1000 − 200) / (2000 − 200) ≈ 0.556
- A service receiving 0 RPS when the 1-hour average was 100 RPS gets a traffic penalty of 0.3
- Overall health for (error: 0.9, latency: 0.556, traffic: 0.7): 0.9×0.5 + 0.556×0.3 + 0.7×0.2 = 0.757 → `degraded`
- A topology with services A→B, B→C, C→A detects a circular dependency
- A gateway service with 6 downstream services is flagged as a gateway

## Acceptance Criteria

- `MetricsCollector` queries Prometheus with correct PromQL for all four golden signals using Linkerd label conventions
- Latency percentiles (p50, p95, p99) are computed correctly from histogram buckets
- `HealthScorer` computes per-metric scores with correct linear degradation formulas
- Overall health score uses the specified weights and classifies correctly as healthy/degraded/critical
- Traffic anomaly detection applies the score penalty when current RPS drops below 10% of average
- `TopologyBuilder` constructs the dependency graph with correct edges and detects circular dependencies
- Gateway and leaf services are correctly identified based on downstream dependency counts
- All outputs marshal to valid JSON with correct field names and timestamp format
- Tests cover metric computation, health scoring edge cases, topology construction, and circular dependency detection
