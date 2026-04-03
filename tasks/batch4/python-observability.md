# Task: Implement an Observability Library with Structured Logging, Metrics, and Correlation IDs for OpenTelemetry Python

## Background

The OpenTelemetry Python repository (https://github.com/open-telemetry/opentelemetry-python) provides observability instrumentation for Python. A new example application module is needed that demonstrates a production observability setup: structured JSON logging with `structlog`, Prometheus-compatible metrics collection, correlation ID propagation through request chains, and middleware that ties all three pillars together into a unified observability layer.

## Files to Create/Modify

- `docs/examples/observability/logging_config.py` (create) — Structured logging configuration with structlog, JSON output, and correlation ID injection
- `docs/examples/observability/metrics_collector.py` (create) — Prometheus-compatible metrics: request counters, latency histograms, error rates, and custom gauge metrics
- `docs/examples/observability/correlation.py` (create) — Correlation ID middleware that generates, propagates, and injects IDs into logs and spans
- `docs/examples/observability/middleware.py` (create) — ASGI middleware that instruments request lifecycle with logging, metrics, and correlation
- `docs/examples/observability/__init__.py` (create) — Package init
- `tests/test_python_observability.py` (create) — Tests for logging, metrics, correlation, and middleware

## Requirements

### Structured Logging (logging_config.py)

- `configure_logging(log_level: str = "INFO", json_output: bool = True)` — configures structlog with ISO-8601 timestamps, log level, stack info, exception formatting
- When `json_output=True`, use `structlog.processors.JSONRenderer()`; when False, use `structlog.dev.ConsoleRenderer()`
- Every log entry must include: `timestamp`, `level`, `event` (message), `logger` (module name), `correlation_id` (from context)
- `get_logger(name: str = None)` — returns a bound structlog logger
- The correlation ID must be injected from a `contextvars.ContextVar` automatically via a custom structlog processor; if no correlation ID is set, use `"no-correlation-id"`

### Metrics Collector (metrics_collector.py)

- `MetricsCollector` class (singleton pattern)
- Metrics:
  - `http_requests_total` — Counter with labels: `method`, `endpoint`, `status_code`
  - `http_request_duration_seconds` — Histogram with labels: `method`, `endpoint`; buckets: `[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]`
  - `http_requests_in_progress` — Gauge with label: `endpoint`
  - `app_errors_total` — Counter with labels: `error_type`, `endpoint`
- `record_request(method, endpoint, status_code, duration)` — increments counter and observes histogram
- `track_in_progress(endpoint)` — context manager that increments gauge on entry, decrements on exit
- `record_error(error_type, endpoint)` — increments error counter
- `get_metrics() -> str` — returns Prometheus text exposition format output
- Label cardinality must be bounded: endpoint must be the route pattern (e.g., `/users/{id}`) not the actual path (`/users/123`)

### Correlation ID (correlation.py)

- `correlation_id_var: ContextVar[str]` — stores the current correlation ID
- `generate_correlation_id() -> str` — generates a UUID4 string
- `get_correlation_id() -> str` — returns current ID or `"no-correlation-id"` if not set
- `set_correlation_id(correlation_id: str)` — sets the ID in the contextvars
- `CorrelationIDMiddleware` (ASGI middleware):
  - Reads `X-Correlation-ID` header from the incoming request; if absent, generates a new one
  - Sets the correlation ID in contextvars for the duration of the request
  - Adds `X-Correlation-ID` response header with the ID
  - Cleans up the contextvar after the request completes

### Observability Middleware (middleware.py)

- `ObservabilityMiddleware` (ASGI middleware) combining all three concerns:
  - Sets correlation ID (via CorrelationIDMiddleware logic)
  - Logs request start (`"Request started"` with method, path, correlation_id) at INFO level
  - Tracks in-progress gauge
  - Records request duration and status in metrics
  - Logs request completion (`"Request completed"` with method, path, status_code, duration_ms) at INFO level
  - On exception: records error metric, logs at ERROR level with exception info, re-raises

### Expected Functionality

- Configuring logging and calling `logger.info("Order created", order_id="123")` outputs `{"timestamp": "...", "level": "info", "event": "Order created", "order_id": "123", "correlation_id": "abc-def"}`
- After handling 100 requests (50 to `/users`, 50 to `/orders`), `get_metrics()` shows `http_requests_total{method="GET",endpoint="/users",status_code="200"} 50`
- An incoming request without `X-Correlation-ID` header gets a generated UUID; subsequent requests with the same header preserve the value
- The middleware logs request start and completion for every request and increments metrics

## Acceptance Criteria

- Structured logging outputs JSON with consistent fields including automatic correlation ID injection
- The console renderer is used when `json_output=False` for development environments
- Metrics collector records counters, histograms, and gauges with bounded label cardinality
- `get_metrics()` returns valid Prometheus text exposition format
- Correlation IDs are generated, propagated via headers and contextvars, and injected into all log entries
- ASGI middleware instruments the full request lifecycle with logging, metrics, and correlation
- Tests verify log output format, metric increments, correlation ID propagation, and middleware behavior
