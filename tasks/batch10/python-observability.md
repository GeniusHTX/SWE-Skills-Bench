# Task: Add Correlation Log Processor to OpenTelemetry Python SDK

## Background
The OpenTelemetry Python SDK (`open-telemetry/opentelemetry-python`) provides tracing and metrics under `opentelemetry-sdk/src/opentelemetry/sdk/`. The `logs/` subpackage implements `LogRecordProcessor` but currently offers no processor that enriches log records with the active span's trace context. Without this, log records and traces cannot be correlated by `trace_id` or `span_id` in backends like Loki or Elasticsearch.

## Files to Create/Modify
- `opentelemetry-sdk/src/opentelemetry/sdk/logs/correlation.py` - `CorrelationLogProcessor` class (new)
- `opentelemetry-sdk/tests/logs/test_correlation.py` - Unit tests for the processor (new)
- `opentelemetry-sdk/src/opentelemetry/sdk/logs/__init__.py` - Export `CorrelationLogProcessor` from the package (modify)

## Requirements

### CorrelationLogProcessor
- Class `CorrelationLogProcessor` must implement `opentelemetry.sdk.logs.LogRecordProcessor`
- `emit(log_record: LogRecord) -> None` must call `opentelemetry.trace.get_current_span()` to obtain the active span
- If the span context is valid (i.e., `span_context.is_valid` is `True`), add these attributes to `log_record.attributes`:
  - `"trace_id"`: lowercase hex string, exactly 32 characters, no `0x` prefix (e.g. `"4bf92f3577b34da6a3ce929d0e0e4736"`)
  - `"span_id"`: lowercase hex string, exactly 16 characters, no `0x` prefix (e.g. `"00f067aa0ba902b7"`)
  - `"trace_flags"`: integer value of `span_context.trace_flags`
- If the span context is not valid, emit `log_record` without adding any attributes
- `shutdown() -> bool` must be a no-op returning `True`
- `force_flush(timeout_millis: int = 30000) -> bool` must be a no-op returning `True`

### Package Export
- Add `CorrelationLogProcessor` to `__init__.py` so it is importable as:
  `from opentelemetry.sdk.logs import CorrelationLogProcessor`

### Unit Tests (`test_correlation.py`)
- `TestEmitWithValidSpan`: create a non-recording span with a known trace ID (`0x4bf92f3577b34da6a3ce929d0e0e4736`) and span ID (`0x00f067aa0ba902b7`) in a `use_span` / context manager; call `emit()` with a `LogRecord`; assert `log_record.attributes["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"` and `log_record.attributes["span_id"] == "00f067aa0ba902b7"`
- `TestEmitNoActiveSpan`: call `emit()` outside any span context; assert `"trace_id"` and `"span_id"` are NOT in `log_record.attributes`
- `TestEmitInvalidSpan`: set `INVALID_SPAN` as current span via `opentelemetry.trace.use_span(INVALID_SPAN)`; assert attributes are NOT added
- `TestShutdownReturnsTrue`: call `shutdown()`; assert return value is `True`
- `TestForceFlushReturnsTrue`: call `force_flush()`; assert return value is `True`

### Expected Functionality
- Active valid span → `trace_id` (32 hex chars), `span_id` (16 hex chars), `trace_flags` (int) added to log record
- No active span context → log record unchanged
- `INVALID_SPAN` active → log record unchanged

## Acceptance Criteria
- `pytest opentelemetry-sdk/tests/logs/test_correlation.py -v` passes all 5 tests
- `trace_id` value length is exactly 32 characters; `span_id` length is exactly 16 characters
- `CorrelationLogProcessor` does not import `structlog`, `logging.basicConfig`, or any third-party logging library
- `from opentelemetry.sdk.logs import CorrelationLogProcessor` succeeds without `ImportError`
- All pre-existing tests in `opentelemetry-sdk/tests/logs/` continue to pass
- `emit()` does not raise when `log_record.attributes` is `None`; it must initialise it to an empty dict first
