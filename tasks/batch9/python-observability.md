# Task: Build a Python Observability Library with Structured Logging, Metrics, and Tracing

## Background

OpenTelemetry Python (https://github.com/open-telemetry/opentelemetry-python) provides observability instrumentation. A new Python observability library is needed that provides a unified API for structured logging (structlog with JSON output), Prometheus metrics (request latency histograms, error counters, active request gauges), distributed tracing (OpenTelemetry spans with context propagation), and correlation ID threading across all three signals.

## Files to Create/Modify

- `src/observability/__init__.py` (create) — Public API exports and `configure()` entry point
- `src/observability/logging.py` (create) — Structured logging setup using structlog with JSON rendering, log level filtering, correlation ID injection, and context variable integration
- `src/observability/metrics.py` (create) — Prometheus metrics registry with `RequestMetrics` class providing histogram, counter, and gauge instruments, plus a WSGI/ASGI middleware for automatic HTTP metrics
- `src/observability/tracing.py` (create) — OpenTelemetry tracing setup with `TracingProvider` class, span creation helpers, context propagation utilities, and a decorator for automatic function tracing
- `src/observability/correlation.py` (create) — Correlation ID management using `contextvars`: generation, propagation, extraction from HTTP headers, and injection into logs/spans/metrics
- `src/observability/middleware.py` (create) — FastAPI middleware that creates spans, records metrics, injects correlation IDs, and adds structured log context for each request
- `tests/test_observability.py` (create) — Unit tests for all modules with mock exporters

## Requirements

### Configuration (`__init__.py`)

- Function `configure(service_name: str, log_level: str = "INFO", enable_tracing: bool = True, enable_metrics: bool = True, otlp_endpoint: Optional[str] = None) -> None`
- Calls each module's setup function with the service name
- Sets up OpenTelemetry TracerProvider with OTLP exporter (or NoOp if not enabled)
- Initializes the metrics registry
- Configures structlog

### Structured Logging (`logging.py`)

- Function `configure_logging(service_name: str, log_level: str = "INFO") -> None` using structlog:
  - Processors: `merge_contextvars`, `add_log_level`, `TimeStamper(fmt="iso")`, `StackInfoRenderer`, `format_exc_info`, `JSONRenderer`
  - Wrapper class: `make_filtering_bound_logger` at the specified level
- Function `get_logger(name: Optional[str] = None) -> BoundLogger` — Returns a structlog logger, optionally bound with `logger_name`
- Every log entry automatically includes: `service`, `correlation_id` (from contextvars), `timestamp`, `level`
- Function `bind_context(**kwargs) -> None` — Adds key-value pairs to structlog context vars for the current async context
- Function `clear_context() -> None` — Clears all bound context vars

### Prometheus Metrics (`metrics.py`)

- Class `RequestMetrics`:
  - `request_duration_seconds` — Histogram with buckets `[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]`, labels: `["method", "endpoint", "status_code"]`
  - `request_errors_total` — Counter with labels: `["method", "endpoint", "error_type"]`
  - `requests_in_progress` — Gauge with labels: `["method", "endpoint"]`
  - Method `observe_request(method, endpoint, status_code, duration)` — Records to histogram and increments/decrements gauge
  - Method `record_error(method, endpoint, error_type)` — Increments error counter
- Function `create_metrics_app() -> Callable` — Returns a WSGI app that serves `/metrics` endpoint in Prometheus exposition format
- All label values must be bounded cardinality (no user IDs, request IDs, or unbounded strings)

### Distributed Tracing (`tracing.py`)

- Function `configure_tracing(service_name: str, otlp_endpoint: Optional[str] = None) -> None` — Sets up OpenTelemetry TracerProvider with:
  - `OTLPSpanExporter` if endpoint provided, else `ConsoleSpanExporter`
  - `BatchSpanProcessor` for async export
  - Resource attributes: `service.name`, `service.version`, `deployment.environment`
- Function `get_tracer(name: str) -> Tracer` — Returns an OpenTelemetry tracer
- Decorator `@traced(name=None, attributes=None)` — Creates a span for the decorated function:
  - Uses function name as span name if `name` is None
  - Sets `attributes` as span attributes
  - Records exceptions as span events with `span.record_exception()`
  - Sets span status to ERROR on exception
- Function `inject_context(headers: dict) -> dict` — Injects current trace context into HTTP headers (W3C TraceContext format)
- Function `extract_context(headers: dict) -> Context` — Extracts trace context from incoming HTTP headers

### Correlation ID (`correlation.py`)

- `ContextVar` `correlation_id` with default `""`
- Function `generate_correlation_id() -> str` — UUID4 hex string
- Function `get_correlation_id() -> str` — Returns current correlation ID from context
- Function `set_correlation_id(cid: str) -> Token` — Sets correlation ID in context, returns reset token
- Function `extract_from_headers(headers: dict, header_name: str = "X-Correlation-ID") -> str` — Extracts correlation ID from HTTP headers; generates new one if not present
- Structlog processor `inject_correlation_id(logger, method, event_dict) -> dict` — Adds `correlation_id` field to every log event

### FastAPI Middleware (`middleware.py`)

- Class `ObservabilityMiddleware(BaseHTTPMiddleware)`:
  - `__init__(app, service_name, metrics: RequestMetrics, excluded_paths: list[str] = ["/health", "/metrics"])`
  - For each request:
    1. Extract or generate correlation ID from `X-Correlation-ID` header
    2. Set correlation ID in contextvars
    3. Create an OpenTelemetry span named `{method} {path}`
    4. Add span attributes: `http.method`, `http.url`, `http.route`, `http.status_code`
    5. Record request duration in metrics histogram
    6. Increment in-progress gauge (decrement on completion)
    7. On 5xx response, record error in metrics
    8. Add `X-Correlation-ID` to response headers
  - Skip all instrumentation for `excluded_paths`

### Expected Functionality

- Calling `configure("my-service")` sets up logging, tracing, and metrics
- A logged message includes `{"service": "my-service", "correlation_id": "abc123", "timestamp": "...", "level": "info", "event": "..."}`
- The `@traced` decorator creates a span and records exceptions as span events
- FastAPI middleware records `request_duration_seconds` histogram for each request with method/endpoint/status labels
- Correlation ID flows from HTTP header → contextvars → log entries → span attributes → outgoing HTTP headers

## Acceptance Criteria

- Structured logging outputs valid JSON with service name, correlation ID, and timestamp in every entry
- Prometheus metrics use bounded-cardinality labels (no user IDs or request bodies)
- Histogram buckets cover the range from 5ms to 10s
- Tracing decorator creates spans with function name and records exceptions
- Correlation ID propagates through the full request lifecycle: header → context → logs → spans → response header
- Middleware skips excluded paths (health/metrics endpoints)
- `python -m pytest /workspace/tests/test_python_observability.py -v --tb=short` passes
