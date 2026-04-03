# Task: Add Structured Logging and Custom Metrics to the WSGI Instrumentation Module

## Background

The OpenTelemetry Python project (https://github.com/open-telemetry/opentelemetry-python) provides instrumentation libraries for common frameworks. The WSGI instrumentation (`opentelemetry-instrumentation-wsgi`) currently emits traces but lacks structured logging with correlation IDs and custom application-level metrics. This task adds structured log output and Prometheus-compatible metrics to the WSGI middleware so that logs, traces, and metrics are correlated.

## Files to Create/Modify

- `instrumentation/opentelemetry-instrumentation-wsgi/src/opentelemetry/instrumentation/wsgi/middleware.py` (modify) — Inject trace context (trace_id, span_id) into log records and emit per-request metrics (latency histogram, request counter, error counter).
- `instrumentation/opentelemetry-instrumentation-wsgi/src/opentelemetry/instrumentation/wsgi/metrics.py` (create) — Define metric instruments: `http_server_request_duration_seconds` (histogram), `http_server_requests_total` (counter), `http_server_errors_total` (counter) with labels `method`, `path`, `status_code`.
- `instrumentation/opentelemetry-instrumentation-wsgi/src/opentelemetry/instrumentation/wsgi/logging_utils.py` (create) — Utility to attach `trace_id` and `span_id` fields to Python log records within the request context.
- `instrumentation/opentelemetry-instrumentation-wsgi/tests/test_metrics.py` (create) — Tests verifying that metrics are emitted with correct labels and values.
- `instrumentation/opentelemetry-instrumentation-wsgi/tests/test_logging_correlation.py` (create) — Tests verifying that log records contain `trace_id` and `span_id` when a trace is active.

## Requirements

### Structured Logging with Trace Context

- During each WSGI request, the middleware must inject `trace_id` and `span_id` as extra fields on all Python `logging` records emitted within that request scope.
- The `trace_id` must match the W3C hex-encoded trace ID from the active span.
- When no trace is active (instrumentation disabled), log records must not contain `trace_id` or `span_id` fields (no `None` values).

### Request Metrics

- `http_server_request_duration_seconds`: Histogram with bucket boundaries `[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]`, labels `method`, `route`, `status_code`.
- `http_server_requests_total`: Counter incremented once per request, labels `method`, `route`, `status_code`.
- `http_server_errors_total`: Counter incremented for responses with `status_code >= 500`, labels `method`, `route`, `status_code`.
- Labels must use bounded cardinality: `route` should be the matched URL pattern (e.g., `/users/{id}`), not the raw path with variable segments.

### Integration

- Metrics and logging instrumentation must be opt-in via middleware configuration parameters: `enable_metrics=True`, `enable_log_correlation=True`.
- When disabled, no metrics are emitted and no log records are modified (zero overhead).
- Metric instruments must be obtained from the global `MeterProvider`, not a hardcoded provider.

### Expected Functionality

- A `GET /api/users/42` returning 200 in 150ms → histogram records 0.15 in bucket `0.25`, counter increments `{method="GET", route="/api/users/{id}", status_code="200"}`.
- A `POST /api/orders` returning 500 → `http_server_errors_total` increments with appropriate labels.
- A log statement `logger.info("processing request")` during an active trace → log record includes `trace_id="abc123..."` and `span_id="def456..."` fields.
- With `enable_metrics=False` → no histogram or counter data is produced.

## Acceptance Criteria

- Log records emitted during a traced WSGI request contain `trace_id` and `span_id` fields matching the active span.
- Three metric instruments are created and correctly record request duration, request count, and error count with bounded-cardinality labels.
- Metric labels use URL patterns (not raw paths) for the `route` label.
- Metrics and log correlation are individually opt-in via middleware configuration.
- All new tests pass and existing WSGI instrumentation tests continue to pass.
