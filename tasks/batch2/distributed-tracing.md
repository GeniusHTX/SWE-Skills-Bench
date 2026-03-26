# Task: Add a Tail-Based Sampling Processor to the OpenTelemetry Collector

## Background

The OpenTelemetry Collector (https://github.com/open-telemetry/opentelemetry-collector) processes telemetry data. A new tail-based sampling processor is needed that makes sampling decisions after a trace is complete, enabling decisions based on full trace characteristics like error status, duration thresholds, or specific attribute values.

## Files to Create

- `processor/tailsamplingprocessor/processor.go` — Tail-based sampling processor implementation (ConsumeTraces, buffer management)
- `processor/tailsamplingprocessor/config.go` — Configuration structures (policies, buffer size, timeout)
- `processor/tailsamplingprocessor/factory.go` — Processor factory with type name registration

## Requirements

### Sampling Logic

- Buffer incoming spans grouped by trace ID until the trace is considered complete (configurable timeout)
- Apply configurable sampling policies to decide whether to keep or drop a trace
- Support at least three policy types:
  - Always sample traces containing error spans
  - Sample traces exceeding a configurable duration threshold
  - Probabilistic sampling at a configurable rate for remaining traces

### Processor Interface

- Implement the collector's processor interface (ConsumeTraces)
- Support pipeline configuration via the collector's configuration system
- Register the processor via a factory with a unique type name

### Resource Management

- Bound the in-memory trace buffer to a configurable maximum size
- Evict oldest traces when the buffer is full
- Clean up expired traces that exceed the decision timeout

## Expected Functionality

- The processor buffers spans and makes sampling decisions after trace completion
- Error traces and high-latency traces are always retained
- Regular traces are sampled probabilistically
- Buffer memory is bounded and cleaned up

## Acceptance Criteria

- Incoming spans are buffered by trace ID until a sampling decision can be made for the complete trace.
- Error traces and traces exceeding the configured latency threshold are retained regardless of the probabilistic sampling rate.
- Remaining traces are sampled according to the configured probabilistic policy.
- Buffer growth is bounded and expired or evicted traces are cleaned up deterministically.
- The processor is configurable through the collector's normal processor registration and pipeline configuration flow.
