# Task: Implement a Custom Trace Processor with Sampling and Tail-Based Analysis for OpenTelemetry Collector

## Background

The OpenTelemetry Collector (https://github.com/open-telemetry/opentelemetry-collector) is a vendor-agnostic agent for collecting, processing, and exporting telemetry data. The project needs a custom trace processor that performs intelligent sampling based on trace characteristics, detects error patterns across spans, and produces trace summary metrics. This should be implemented as a new processor component following the Collector's component architecture.

## Files to Create/Modify

- `processor/traceanalysisprocessor/factory.go` (create) — Component factory registration
- `processor/traceanalysisprocessor/config.go` (create) — Configuration struct with validation
- `processor/traceanalysisprocessor/processor.go` (create) — Trace processor implementation with sampling and analysis logic
- `processor/traceanalysisprocessor/processor_test.go` (create) — Tests for the processor

## Requirements

### Component Setup

- Register the processor with type string `"trace_analysis"`
- Configuration struct with fields: `sampling_rate` (float, 0.0–1.0, default 1.0), `error_sampling_rate` (float, 0.0–1.0, default 1.0 — always keep error traces), `latency_threshold_ms` (int, default 5000 — threshold for high-latency trace detection), `max_traces_per_second` (int, default 0 — 0 means unlimited), `analysis_enabled` (bool, default true)
- Validate configuration: `sampling_rate` and `error_sampling_rate` must be 0.0–1.0; `latency_threshold_ms` must be ≥ 0; return error for invalid values
- Implement the `processor.Traces` interface: `ConsumeTraces(ctx context.Context, td ptrace.Traces) error`

### Intelligent Sampling

- **Base sampling**: Sample traces at `sampling_rate`; use a deterministic hash of the trace ID so the same trace is always sampled or dropped consistently
- **Error-priority sampling**: Traces containing at least one span with `StatusCode == Error` are sampled at `error_sampling_rate` (typically 1.0 to keep all errors)
- **Latency-priority sampling**: Traces where the root span duration exceeds `latency_threshold_ms` are always kept (sampling rate 1.0)
- **Rate limiting**: If `max_traces_per_second > 0`, enforce a token-bucket rate limit; excess traces are dropped even if they would otherwise be sampled
- When a trace is dropped, increment a counter metric `traces_dropped_total` with labels `reason` = `"sampling"`, `"rate_limit"`

### Trace Analysis

- For each passing trace, compute and add as resource attributes:
  - `trace.span_count` — total number of spans in the trace
  - `trace.depth` — maximum nesting depth of spans (root = depth 1)
  - `trace.duration_ms` — duration of the root span in milliseconds
  - `trace.has_errors` — boolean, whether any span has an error status
  - `trace.service_count` — number of distinct `service.name` values across spans
- Detect "orphan spans" — spans whose parent span ID is set but the parent is not present in the trace batch; log a warning with the span ID and expected parent ID

### Error Pattern Detection

- If analysis is enabled, track error spans and detect patterns:
  - Count errors by `service.name` and span `name`; if any combination exceeds 10 errors within a 1-minute window, add a `trace.error_pattern_detected` attribute with value `true`
- For error spans, extract the exception type from span events (event name `"exception"`, attribute `"exception.type"`) and add it as `trace.exception_type` attribute on the trace

### Expected Functionality

- With `sampling_rate=0.5`, approximately half of non-error, non-slow traces are dropped; the same trace ID always gets the same decision
- A trace with an error span is kept even at `sampling_rate=0.1` (because `error_sampling_rate=1.0`)
- A trace with root span duration 6000ms is kept regardless of sampling rate (latency priority)
- With `max_traces_per_second=100`, the 101st trace in a 1-second window is dropped with reason `rate_limit`
- A trace with spans from 3 services has `trace.service_count = 3`
- A trace with max nesting root→child→grandchild has `trace.depth = 3`

## Acceptance Criteria

- The processor registers as `trace_analysis` and validates all configuration fields
- Deterministic sampling produces consistent keep/drop decisions for the same trace ID
- Error-priority and latency-priority sampling override the base sampling rate
- Rate limiting drops excess traces and increments `traces_dropped_total` with the correct reason label
- Trace analysis attributes (`span_count`, `depth`, `duration_ms`, `has_errors`, `service_count`) are correctly computed and added
- Orphan spans are detected and logged at warning level
- Error pattern detection identifies repeated error combinations within the 1-minute window
- Tests cover sampling decisions, rate limiting, attribute computation, orphan detection, and error patterns
