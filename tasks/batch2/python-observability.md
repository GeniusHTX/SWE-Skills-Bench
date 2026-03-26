# Task: Create an Observability Demonstration Script for OpenTelemetry Python

## Background

OpenTelemetry Python (https://github.com/open-telemetry/opentelemetry-python) provides APIs and SDKs for distributed observability. A demonstration script is needed under `docs/examples/` that shows how to set up structured logging, record custom metrics, and create distributed traces in a single cohesive example.

## Files to Create

- `docs/examples/observability_demo.py` — A self-contained demonstration of OpenTelemetry observability primitives

## Requirements

### Tracing

- Initialize a TracerProvider with a configurable exporter (console or OTLP)
- Create nested spans simulating a request flow (e.g., HTTP handler → database query → cache lookup)
- Attach span attributes for request metadata (method, path, status code)
- Propagate context across span boundaries

### Metrics

- Initialize a MeterProvider and create a Meter
- Record at least two metric types: a counter (e.g., request count) and a histogram (e.g., request duration)
- Attach labels/attributes to metric recordings

### Logging

- Set up structured logging that correlates with active trace IDs
- Log events at different severity levels (info, warning, error) with structured fields
- Demonstrate log-trace correlation by including trace and span IDs in log output

### Output

- The script must have a `__main__` entry point
- Running it produces observable output (console traces, metrics, and structured logs)

## Expected Functionality

- The script demonstrates all three observability signals (traces, metrics, logs) working together
- Trace IDs appear in log messages, enabling correlation
- All spans, metrics, and logs are emitted to configured exporters

## Acceptance Criteria

- The example emits all three observability signals together: traces, metrics, and structured logs.
- Trace and span context is visible in log output so requests can be correlated across signals.
- The trace example includes nested spans with realistic attributes representing a request flow.
- Metrics include at least one counter and one histogram with useful attributes.
- The script can be executed as a standalone demonstration and produces understandable observable output.
