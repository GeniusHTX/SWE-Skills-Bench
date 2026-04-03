# Task: Add a Traffic Health Summary Dashboard Generator to Linkerd Viz

## Background

Linkerd's viz extension provides observability for service mesh traffic. A new CLI subcommand and supporting Go library are needed to generate a traffic health summary report for a given namespace. The report aggregates golden signal metrics (latency percentiles, request rate, error rate, saturation) across all meshed deployments in the namespace and outputs a structured JSON or human-readable table suitable for CI integration or operational review.

## Files to Create/Modify

- `viz/cmd/health_summary.go` (new) — CLI subcommand `linkerd viz health-summary` that accepts namespace, output format, and time window flags
- `viz/pkg/healthsummary/aggregator.go` (new) — Core aggregation logic that queries Prometheus metrics and computes per-deployment and namespace-level golden signal summaries
- `viz/pkg/healthsummary/aggregator_test.go` (new) — Unit tests for the aggregation logic using mock metrics data
- `viz/pkg/healthsummary/types.go` (new) — Data types for health summary reports (deployment entry, namespace summary, signal values)
- `viz/cmd/root.go` (modify) — Register the new `health-summary` subcommand in the viz CLI command tree

## Requirements

### CLI Interface

- The command `linkerd viz health-summary --namespace <ns>` produces a health report for all meshed deployments in the given namespace
- `--output` flag accepts `json` or `table` (default: `table`)
- `--window` flag accepts a Prometheus duration string (e.g., `5m`, `1h`; default: `5m`)
- If the namespace has no meshed deployments, the command must exit with code 0 and print a clear "no meshed deployments found" message
- If the Prometheus API is unreachable, the command must exit with code 1 and print an actionable error message

### Golden Signal Aggregation

- For each meshed deployment, compute:
  - **Request rate**: requests per second over the time window
  - **Error rate**: percentage of responses with HTTP status >= 500
  - **Latency P50, P95, P99**: in milliseconds, derived from response latency histograms
  - **Saturation**: active TCP connections as a fraction of a configurable max (default: 1000)
- The namespace-level summary must contain the aggregate (weighted average by request count) of all deployment-level signals
- Deployments with zero requests in the time window must appear in the report with all signal values as `null` in JSON or `—` in table format

### JSON Output Format

- Top-level fields: `namespace`, `window`, `generated_at` (RFC 3339), `summary` (namespace-level signals), `deployments` (array)
- Each deployment entry: `name`, `request_rate`, `error_rate`, `latency_p50`, `latency_p95`, `latency_p99`, `saturation`, `status` ("healthy", "degraded", "critical")
- Status determination: "critical" if error_rate > 10% or P99 latency > 5000ms; "degraded" if error_rate > 1% or P99 latency > 1000ms; "healthy" otherwise
- Deployments with zero requests have status `"unknown"`

### Table Output Format

- Header row followed by one row per deployment, sorted by status (critical first, then degraded, healthy, unknown)
- Columns: `DEPLOYMENT`, `STATUS`, `RPS`, `ERR%`, `P50`, `P95`, `P99`, `SATURATION`
- Numeric values formatted to 2 decimal places; latencies in milliseconds with "ms" suffix
- A footer row with the namespace-level summary

### Expected Functionality

- Namespace with 3 deployments (web: 100 rps/0.5% errors/P99=800ms, api: 50 rps/12% errors/P99=6000ms, worker: 0 rps) → JSON output shows web as "healthy", api as "critical", worker as "unknown"; namespace summary weighted by request count
- `--output table` for same data shows api first (critical), web second (healthy), worker third (unknown), with footer showing weighted averages
- `--namespace nonexistent-ns` with no meshed deployments → exit 0, message "no meshed deployments found in namespace nonexistent-ns"
- `--window 1h` correctly passes the window parameter to Prometheus queries
- Prometheus unreachable → exit code 1, error message containing the connection failure reason

## Acceptance Criteria

- `linkerd viz health-summary --namespace <ns>` produces a correctly structured health report aggregating golden signals for all meshed deployments
- Status classification (healthy/degraded/critical/unknown) follows the defined thresholds and appears correctly in both JSON and table output
- Deployments with zero traffic are included with null/dash signal values and "unknown" status
- The namespace-level summary in JSON output contains weighted average signal values
- Table output sorts deployments by severity and includes a footer summary row
- The command exits cleanly with code 0 for empty namespaces and code 1 for Prometheus connectivity failures
- `go build ./viz/...` succeeds with the new code included
- Unit tests cover weighted aggregation, status classification, zero-traffic deployments, and output formatting
