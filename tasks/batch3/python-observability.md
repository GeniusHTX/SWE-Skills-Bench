# Task: Add Structured Logging and Metrics Instrumentation to OpenTelemetry Python SDK

## Background

The OpenTelemetry Python SDK (https://github.com/open-telemetry/opentelemetry-python) provides observability APIs and SDK implementations. The `opentelemetry-sdk` package needs an enhanced logging exporter that produces structured JSON logs with trace correlation, and a new metrics middleware component that tracks the four golden signals (latency, traffic, errors, saturation) for HTTP services. These components should integrate with the existing SDK architecture.

## Files to Create/Modify

- `opentelemetry-sdk/src/opentelemetry/sdk/logs/structured_formatter.py` (create) — JSON log formatter that includes trace/span IDs, service metadata, and structured fields
- `opentelemetry-sdk/src/opentelemetry/sdk/metrics/http_signals.py` (create) — HTTP middleware metrics collector tracking latency, request count, error rate, and concurrent requests
- `opentelemetry-sdk/tests/logs/test_structured_formatter.py` (create) — Tests for the structured log formatter
- `opentelemetry-sdk/tests/metrics/test_http_signals.py` (create) — Tests for the HTTP signals metrics collector

## Requirements

### Structured JSON Log Formatter

- Implement a `StructuredFormatter` class compatible with Python's `logging.Formatter`
- Each log record must be serialized as a single-line JSON object with fields: `timestamp` (ISO 8601 with timezone), `level` (string), `message` (string), `logger` (logger name), `trace_id` (hex string or null), `span_id` (hex string or null), `service.name` (from Resource), `service.version` (from Resource)
- If a current active span exists, extract `trace_id` and `span_id` from the span context; otherwise set them to `null`
- Support adding arbitrary structured fields via a `extra` dict on the log record, merged into the top-level JSON
- Ensure all JSON output is valid even when log messages contain special characters (quotes, newlines, unicode)
- The formatter must never raise an exception; if serialization fails, output a fallback plain-text record

### HTTP Golden Signals Metrics

- Implement an `HttpSignalsCollector` class that tracks:
  - **Latency**: Histogram of request duration in seconds, with labels `method`, `path`, `status_code`
  - **Traffic**: Counter of total requests, with labels `method`, `path`
  - **Errors**: Counter of error responses (status >= 500), with labels `method`, `path`, `status_code`
  - **Saturation**: UpDownCounter of concurrent in-flight requests, with label `method`
- Use the OpenTelemetry Metrics API (`opentelemetry.metrics`) to create instruments
- The `path` label must be normalized: strip query parameters, replace numeric path segments with `{id}` (e.g., `/users/42/orders` becomes `/users/{id}/orders`) to prevent unbounded cardinality
- Provide `before_request(method, path)` and `after_request(method, path, status_code, duration_seconds)` methods for framework-agnostic integration
- `before_request` increments the saturation counter; `after_request` decrements it, records the histogram, and increments traffic/error counters

### Cardinality Protection

- The path normalization must handle: numeric segments, UUIDs (replace with `{uuid}`), and configurable custom patterns via a `path_patterns` parameter (list of regex→replacement pairs)
- If the total number of unique `(method, path)` combinations exceeds a configurable `max_cardinality` (default: 1000), new paths are bucketed under `{other}` to prevent metric explosion

### Expected Functionality

- A log message emitted inside an active span includes the correct `trace_id` and `span_id` in the JSON output
- A log message emitted outside any span has `trace_id: null` and `span_id: null`
- A log message containing `"key": "value"` in the message text produces valid JSON output
- After processing 100 requests to `/users/42` with status 200, the traffic counter for path `/users/{id}` reads 100
- After processing 5 requests with status 500, the errors counter reads 5
- During 3 concurrent requests, the saturation gauge reads 3; after all complete, it reads 0
- A path `/api/v1/users/550e8400-e29b-41d4-a716-446655440000/profile` is normalized to `/api/v1/users/{uuid}/profile`

## Acceptance Criteria

- `StructuredFormatter` produces valid single-line JSON for every log record, including edge cases with special characters
- Trace and span IDs are correctly extracted from the active span context and included in log output
- `HttpSignalsCollector` records latency, traffic, errors, and saturation using OpenTelemetry metric instruments
- Path normalization replaces numeric segments with `{id}` and UUIDs with `{uuid}`, preventing unbounded cardinality
- Cardinality protection buckets paths under `{other}` when unique combinations exceed `max_cardinality`
- The saturation counter correctly tracks concurrent in-flight requests (increments on start, decrements on end)
- The formatter never raises exceptions; serialization failures produce a fallback plain-text output
- Tests cover normal flows, trace correlation, special characters, path normalization patterns, cardinality limits, and concurrent request tracking
