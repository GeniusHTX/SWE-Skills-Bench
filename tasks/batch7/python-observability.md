# Task: Add OpenTelemetry Instrumentation to the Python SDK's HTTP Exporter

## Background

The OpenTelemetry Python SDK (https://github.com/open-telemetry/opentelemetry-python) provides exporters for sending telemetry data to backends. The task is to add structured logging, Prometheus metrics, and self-tracing instrumentation to the `OTLPExporterMixin` class in the OTLP HTTP exporter, so that users can observe the exporter's own performance and diagnose export failures.

## Files to Create/Modify

- `exporter/opentelemetry-exporter-otlp-proto-http/src/opentelemetry/exporter/otlp/proto/http/_log_exporter/__init__.py` (modify) — Add structured logging for export attempts, successes, and failures using `structlog`
- `exporter/opentelemetry-exporter-otlp-proto-http/src/opentelemetry/exporter/otlp/proto/http/exporter.py` (modify) — Add Prometheus counter/histogram metrics to `OTLPExporterMixin._export` method
- `exporter/opentelemetry-exporter-otlp-proto-http/src/opentelemetry/exporter/otlp/proto/http/metrics.py` (create) — Define the Prometheus metrics instruments for the exporter's self-monitoring
- `exporter/opentelemetry-exporter-otlp-proto-http/tests/test_exporter_observability.py` (create) — Unit tests verifying the metrics and logging behavior

## Requirements

### Prometheus Metrics (`metrics.py`)

Define the following metrics using the `prometheus_client` library:

```python
from prometheus_client import Counter, Histogram, Gauge

OTLP_EXPORT_REQUESTS_TOTAL = Counter(
    "otlp_exporter_export_requests_total",
    "Total number of export requests made by the OTLP HTTP exporter",
    labelnames=["exporter_type", "signal", "status"],  # status: "success" | "failed" | "retried"
)

OTLP_EXPORT_DURATION_SECONDS = Histogram(
    "otlp_exporter_export_duration_seconds",
    "Duration of individual OTLP export requests in seconds",
    labelnames=["exporter_type", "signal"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

OTLP_EXPORT_ITEMS_TOTAL = Counter(
    "otlp_exporter_items_exported_total",
    "Total number of spans/metrics/log records exported",
    labelnames=["exporter_type", "signal", "status"],
)

OTLP_EXPORT_QUEUE_SIZE = Gauge(
    "otlp_exporter_queue_size",
    "Current number of batches waiting to be exported",
    labelnames=["exporter_type", "signal"],
)
```

- `exporter_type`: `"otlp_http"` (always for this exporter)
- `signal`: `"traces"`, `"metrics"`, or `"logs"` — determined by the exporter subclass

### `OTLPExporterMixin` Modifications (`exporter.py`)

#### Add `_export` Instrumentation

Wrap the existing `_export(serialized_data, timeout, signal_type)` method logic to:

1. **Record export duration**: Time the HTTP POST request using `OTLP_EXPORT_DURATION_SECONDS.labels(...)` with `time()` context manager pattern
2. **Count export requests**: After the HTTP call completes:
   - Status `"success"` if response HTTP 200
   - Status `"retried"` if the exporter retried due to 503/429 (use retry count from existing retry logic)
   - Status `"failed"` if the export failed with an error or HTTP 4xx/5xx after retries
3. **Count items exported**: `OTLP_EXPORT_ITEMS_TOTAL` must increment with the count of spans/metric points/log records in the batch (use the `len(serialized_data)` of the proto messages)
4. **Do not break existing behavior**: All metrics recording is best-effort — if a metric recording raises an exception, log it at DEBUG level and continue the export without interruption

### Structured Logging (`__init__.py` and `exporter.py`)

Replace bare `logging` calls with `structlog` in the OTLP HTTP exporter. Specifically:

- `logger.warning("...")` → `logger.warning("...", key=value, ...)` with structured context fields
- On export attempt:
  ```python
  logger.debug(
      "otlp_export_started",
      endpoint=self._endpoint,
      signal=signal_type,
      item_count=len(serialized_data),
  )
  ```
- On export success:
  ```python
  logger.debug(
      "otlp_export_success",
      endpoint=self._endpoint,
      signal=signal_type,
      duration_ms=round(duration * 1000, 2),
      http_status=response.status_code,
  )
  ```
- On export failure:
  ```python
  logger.warning(
      "otlp_export_failed",
      endpoint=self._endpoint,
      signal=signal_type,
      http_status=getattr(response, "status_code", None),
      error=str(exc),
      retries=retry_count,
  )
  ```

Logger configuration must NOT alter the root logger — use `structlog.get_logger(__name__)` bound to the module.

### Signal Type Detection

Add a `_signal_type` class attribute to each exporter subclass:
- `OTLPSpanExporter._signal_type = "traces"`
- `OTLPMetricExporter._signal_type = "metrics"`
- `OTLPLogExporter._signal_type = "logs"`

Use this attribute in `OTLPExporterMixin._export` to populate metric labels.

## Expected Functionality

- After exporting a batch of 100 spans successfully, `OTLP_EXPORT_REQUESTS_TOTAL.labels("otlp_http", "traces", "success")` value is 1 and `OTLP_EXPORT_ITEMS_TOTAL.labels("otlp_http", "traces", "success")` value is 100
- When the server returns 503 and the exporter retries twice before giving up, `status="retried"` counter increments twice and `status="failed"` increments once
- Export duration histogram has at least one observation in its buckets after a successful export
- If `prometheus_client` raises an exception during `labels()`, the export still completes
- Structured log lines contain `endpoint`, `signal`, and `duration_ms` fields

## Acceptance Criteria

- All four Prometheus metrics are defined in `metrics.py` with correct names, help strings, labels, and buckets
- `_export` records duration, request count, item count, and uses correct `status` label values
- Structured log calls use `structlog.get_logger(__name__)` and include required context fields
- `_signal_type` is set to `"traces"`, `"metrics"`, or `"logs"` on the appropriate subclasses
- Metrics recording failures do not interrupt or fail the export
- Unit tests mock the HTTP transport and Prometheus registry, and verify counter increments and histogram observations
- All existing OTLP HTTP exporter tests continue to pass
