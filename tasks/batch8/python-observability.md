# Task: Add Structured Logging and Metric Instrumentation to OpenTelemetry SDK Example

## Background

The OpenTelemetry Python project (https://github.com/open-telemetry/opentelemetry-python) provides the reference implementation of the OpenTelemetry API and SDK for Python. The project's `opentelemetry-sdk/` package includes metric instruments and exporters but lacks a comprehensive, self-contained example demonstrating how to instrument a Python HTTP service with structured logging correlated to traces, custom metrics with bounded cardinality, and request-scoped context propagation. A new example package is needed under the existing `docs/` or `tests/` area.

## Files to Create/Modify

- `docs/examples/instrumented_service/app.py` (create) — A simple HTTP service (using `http.server`) instrumented with OpenTelemetry traces, metrics, and structured logging
- `docs/examples/instrumented_service/instrumentation.py` (create) — Centralized instrumentation setup: `TracerProvider`, `MeterProvider`, log formatter, and correlation ID propagation
- `docs/examples/instrumented_service/metrics.py` (create) — Custom metric definitions: request counter, latency histogram, active request gauge, and error rate counter
- `docs/examples/instrumented_service/middleware.py` (create) — Request middleware that starts spans, records metrics, injects correlation IDs, and emits structured log entries
- `docs/examples/instrumented_service/README.md` (create) — Usage and configuration instructions
- `tests/test_instrumented_service.py` (create) — Tests verifying span creation, metric recording, correlation ID propagation, and log output format

## Requirements

### Trace Instrumentation

- Every incoming HTTP request must create a new span with attributes: `http.method`, `http.url`, `http.status_code`, `http.route`
- Span names must follow the format `"{method} {route}"` (e.g., `"GET /items"`)
- Nested operations (e.g., database queries, external calls) must create child spans within the request span
- Spans for failed requests must set `StatusCode.ERROR` and record the exception as a span event
- The trace ID and span ID must be extractable from the active span context for log correlation

### Metric Instruments

- `http_requests_total` — Counter tracking total HTTP requests, with attributes `method`, `route`, `status_code`
- `http_request_duration_seconds` — Histogram recording request latency in seconds, with attributes `method`, `route`; must use explicit bucket boundaries `[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]`
- `http_requests_active` — UpDownCounter tracking currently in-flight requests, with attribute `method`
- `http_errors_total` — Counter tracking requests resulting in 5xx status codes, with attributes `method`, `route`, `error_type`
- Metric attribute values must have bounded cardinality: `route` must be the route template (e.g., `/items/{id}`), not the actual path with parameter values (e.g., `/items/42`); `error_type` must be the exception class name, not the full message

### Structured Logging

- Log entries must be JSON-formatted with fields: `timestamp` (ISO 8601), `level`, `message`, `trace_id`, `span_id`, `correlation_id`, `method`, `path`
- The `trace_id` and `span_id` fields must match the active OpenTelemetry span context; if no span is active, these fields must be empty strings
- A `correlation_id` must be read from the `X-Correlation-ID` request header if present, or generated as a UUID4 if absent
- The correlation ID must propagate through all log entries and child spans for the same request using Python's `contextvars`

### Context Propagation

- The `X-Correlation-ID` header must be injected into outgoing responses
- If the service makes downstream HTTP calls, the correlation ID and W3C `traceparent` header must be propagated to the downstream request
- The correlation ID must be added as a span attribute `correlation_id` on the root request span

### HTTP Service Endpoints

- `GET /items` — returns a JSON list of mock items; demonstrates successful request instrumentation
- `GET /items/{id}` — returns a single item or 404; demonstrates route-parameterized metrics
- `POST /items` — creates an item; demonstrates write operation tracing
- `GET /error` — always raises an unhandled exception; demonstrates error span recording and 5xx metric increment
- `GET /slow` — sleeps 2 seconds; demonstrates latency histogram recording

## Expected Functionality

- `GET /items` produces a span named `"GET /items"` with `http.status_code=200`, increments `http_requests_total{method="GET", route="/items", status_code="200"}`, and records a latency measurement in `http_request_duration_seconds`
- `GET /items/42` records metric attribute `route="/items/{id}"` (not `route="/items/42"`) to maintain bounded cardinality
- `GET /error` produces a span with `StatusCode.ERROR`, records the exception, and increments `http_errors_total{error_type="ValueError"}`
- Log entries for a request include the matching `trace_id` and `span_id` from the active span
- A request with header `X-Correlation-ID: abc-123` propagates `abc-123` through all logs, spans, and the response header
- `GET /slow` records a latency measurement of approximately 2.0 seconds in the histogram

## Acceptance Criteria

- Every HTTP request creates an OpenTelemetry span with the required attributes and correct status codes
- Four metric instruments (counter, histogram, up-down counter, error counter) are recorded with bounded-cardinality attributes
- Log entries are JSON-formatted and include `trace_id`, `span_id`, and `correlation_id` correlated to the active span context
- Correlation IDs are propagated from request headers (or generated), included in spans and logs, and returned in response headers
- Metric attribute `route` uses route templates, not actual paths with parameter values
- Error spans record the exception and set error status; 5xx responses increment the error counter
- The test suite validates span creation, metric values, log format, and correlation ID propagation
