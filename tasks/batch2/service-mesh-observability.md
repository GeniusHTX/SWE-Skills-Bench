# Task: Add a Mesh-Wide Metrics Aggregation Dashboard to Linkerd Viz

## Background

Linkerd (https://github.com/linkerd/linkerd2) includes a `viz` extension for observability. New functionality is needed in the `viz` component that aggregates service mesh metrics across all namespaces and exposes summary data for mesh-wide health monitoring — including success rates, latency percentiles, and request volume by service.

## Files to Create

- `viz/metrics/aggregator.go` — Mesh-wide metrics aggregation logic (per-service and summary stats)
- `viz/metrics/types.go` — Go structs for service-level metrics and mesh-wide summaries
- `viz/metrics/handler.go` — HTTP endpoint handler returning aggregated metrics as JSON

## Requirements

### Metrics Aggregation

- Aggregate per-service metrics: request rate, success rate, and latency percentiles (p50, p95, p99)
- Support aggregation across all meshed namespaces or filtered by a specific namespace
- Calculate mesh-wide summary statistics (total request volume, overall success rate)

### Data Model

- Define Go structs for service-level metrics and mesh-wide summaries
- Support time-windowed aggregation (e.g., last 1 minute, 5 minutes, 1 hour)
- Handle services with zero traffic gracefully

### API Endpoint

- Expose an HTTP endpoint that returns the aggregated metrics as JSON
- Support query parameters for namespace filtering and time window selection
- Return appropriate HTTP status codes for error cases

### Build

- All Go source files must compile as part of the Linkerd viz module

## Expected Functionality

- Querying the endpoint returns a JSON summary of mesh-wide metrics
- Filtering by namespace returns only metrics for services in that namespace
- Services with no recent traffic are included with zero values

## Acceptance Criteria

- The metrics endpoint returns mesh-wide summaries and per-service metrics in a structured JSON response.
- Namespace filtering limits the returned service set without breaking aggregate calculations.
- Reported metrics include request rate, success rate, and latency percentiles for each service.
- Services with no recent traffic are represented safely with zero-valued metrics instead of being omitted unexpectedly.
- Supported time-window selection changes the aggregation scope in a predictable way.
