# Task: Add End-to-End Observability Demo for OpenTelemetry Python

## Background

Add a comprehensive observability demonstration script to the opentelemetry-python repository that shows manual instrumentation with tracing, context propagation, and metric collection.

## Files to Create/Modify

- `docs/examples/observability_demo.py` - Main demo script combining tracing and context propagation

## Requirements

### Tracing
- `TracerProvider` configuration with `ConsoleSpanExporter`
- Creating and nesting spans
- Adding span attributes and events
- Exception recording with proper span status

### Context Propagation
- W3C TraceContext format (`traceparent`, `tracestate` headers)
- HTTP header injection for outgoing requests
- Context extraction from incoming request headers
- Cross-service trace correlation demonstration

### Additional Features
- Span links for async workflows
- Baggage for cross-cutting data
- Resource detection
- Proper span error handling and status codes

### Output
- The script must produce trace output with valid `trace_id` format (32-char hex)
- Nested spans must appear with correct parent relationships

## Acceptance Criteria

- `python docs/examples/observability_demo.py` exits with code 0
- Output shows `trace_id` in correct 32-character hex format
- Spans are properly nested and context propagates correctly
