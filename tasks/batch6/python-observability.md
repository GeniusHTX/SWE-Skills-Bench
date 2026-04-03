# Task: Add Structured Logging and Correlation ID Tracing to OpenTelemetry Python Demo Service

## Background

The OpenTelemetry Python repository (https://github.com/open-telemetry/opentelemetry-python) provides instrumentation libraries for distributed systems. A demo HTTP service is needed that showcases structured logging with correlation IDs, custom span processing, and metric collection — demonstrating how to combine all three observability signals (logs, traces, metrics) in a single Python application using the OpenTelemetry SDK.

## Files to Create/Modify

- `docs/examples/observability_demo/app.py` (create) — A FastAPI application with three endpoints that demonstrates structured logging, distributed tracing, and metric recording
- `docs/examples/observability_demo/logging_config.py` (create) — Structured logging configuration using structlog with JSON output and correlation ID injection from trace context
- `docs/examples/observability_demo/tracing_config.py` (create) — OpenTelemetry tracer provider setup with a custom `SpanProcessor` that enriches spans with request metadata
- `docs/examples/observability_demo/metrics_config.py` (create) — OpenTelemetry meter provider setup with request duration histogram, active request gauge, and error counter
- `docs/examples/observability_demo/middleware.py` (create) — FastAPI middleware that generates/propagates correlation IDs, records request metrics, and binds log context
- `tests/test_observability_demo.py` (create) — Tests verifying correlation ID propagation, log structure, span attributes, and metric recording

## Requirements

### Structured Logging

- Configure `structlog` to output JSON-formatted log entries with the following mandatory fields on every log line: `timestamp` (ISO 8601), `level`, `event` (message), `correlation_id`, `service_name`.
- The `correlation_id` must be extracted from the current OpenTelemetry span's trace ID if available, or from an incoming `X-Correlation-ID` HTTP header, or generated as a new UUID if neither exists.
- Log levels must follow semantic conventions: `INFO` for request lifecycle events, `WARNING` for retries and fallbacks, `ERROR` for unhandled exceptions with full stack traces.

### Correlation ID Middleware

- A FastAPI middleware must:
  1. Extract `X-Correlation-ID` from the incoming request header (or generate a UUID).
  2. Store the correlation ID in a `contextvars.ContextVar`.
  3. Bind the correlation ID to structlog's context so all subsequent logs include it.
  4. Add the correlation ID as a span attribute (`app.correlation_id`) on the current trace span.
  5. Return the correlation ID in the response `X-Correlation-ID` header.
- The middleware must also record request duration and increment the request counter metric.

### Custom Span Processor

- Implement a `MetadataSpanProcessor` extending `opentelemetry.sdk.trace.SpanProcessor`.
- On `on_start`, the processor must add the following attributes to every span: `service.instance.id` (a fixed instance identifier), `deployment.environment` (from config).
- On `on_end`, the processor must log a structured message at `DEBUG` level with span name, duration in milliseconds, and status code.

### Metrics

- Create the following instruments using the OpenTelemetry Meter API:
  - `http_request_duration_seconds` — a Histogram recording request latency with labels: `method`, `path`, `status_code`.
  - `http_requests_active` — an UpDownCounter tracking in-flight requests with label: `method`.
  - `http_requests_total` — a Counter for total requests with labels: `method`, `path`, `status_code`.
  - `http_request_errors_total` — a Counter for requests resulting in 4xx or 5xx responses, with labels: `method`, `path`, `status_code`.
- Label cardinality must be bounded — use the route template (e.g., `/items/{item_id}`) not the actual path (e.g., `/items/123`).

### Demo Endpoints

- `GET /health` — returns `{"status": "ok"}`, logs at INFO level.
- `GET /items/{item_id}` — returns a mock item JSON. If `item_id` is `"error"`, raises an HTTP 500 to demonstrate error tracing. If `item_id` is `"slow"`, sleeps 2 seconds to demonstrate latency tracking.
- `POST /items` — accepts a JSON body with `name` (str) and `price` (float), returns the created item with an auto-generated ID. Logs the creation event at INFO level with the item ID.

### Expected Functionality

- `GET /items/42` with header `X-Correlation-ID: abc-123` → response includes header `X-Correlation-ID: abc-123`, all log entries during the request contain `"correlation_id": "abc-123"`, the trace span has attribute `app.correlation_id=abc-123`.
- `GET /items/42` without `X-Correlation-ID` header → a new UUID is generated, returned in the response header, and present in all logs and span attributes.
- `GET /items/error` → HTTP 500 response, `http_request_errors_total` counter incremented, error logged at `ERROR` level with stack trace and correlation ID.
- `GET /items/slow` → response after ~2 seconds, `http_request_duration_seconds` records ~2.0, `http_requests_active` increments to 1 during the request and decrements to 0 after.
- Every log line is valid JSON containing at minimum: `timestamp`, `level`, `event`, `correlation_id`, `service_name`.

## Acceptance Criteria

- All log output is structured JSON with `timestamp`, `level`, `event`, `correlation_id`, and `service_name` fields present on every line.
- Correlation IDs propagate from incoming `X-Correlation-ID` headers through logs, trace span attributes, and back to response headers.
- A custom `SpanProcessor` enriches every span with `service.instance.id` and `deployment.environment` attributes.
- Four OpenTelemetry metric instruments are created with bounded-cardinality labels using route templates.
- The `/items/error` endpoint triggers error counting and ERROR-level structured logging with stack trace.
- The `/items/slow` endpoint demonstrates measurable request duration in both the histogram metric and the trace span.
- Tests verify correlation ID round-trip, log JSON structure, span attribute presence, and metric instrument creation.
