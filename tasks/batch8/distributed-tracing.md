# Task: Implement a Custom Span Processor and Exporter for OpenTelemetry Collector

## Background

The OpenTelemetry Collector receives, processes, and exports telemetry data (traces, metrics, logs) from instrumented applications. A new custom processor is needed that enriches trace spans with deployment metadata and detects high-latency request chains by analyzing parent-child span relationships. This processor should integrate into the Collector's pipeline and work alongside a companion file-based exporter for debugging trace output.

## Files to Create/Modify

- `processor/deploymentprocessor/factory.go` (new) — Factory registration for the deployment metadata processor, including config defaults and pipeline binding
- `processor/deploymentprocessor/processor.go` (new) — Core processor logic that enriches spans with deployment attributes and flags latency anomalies
- `processor/deploymentprocessor/config.go` (new) — Configuration struct for the processor (thresholds, attribute keys, deployment labels)
- `processor/deploymentprocessor/processor_test.go` (new) — Unit tests for span enrichment and latency detection logic
- `exporter/filetraceexporter/factory.go` (new) — Factory registration for a file-based trace exporter
- `exporter/filetraceexporter/exporter.go` (new) — Exporter that writes processed trace spans to a structured JSON file
- `exporter/filetraceexporter/exporter_test.go` (new) — Unit tests for the file exporter

## Requirements

### Processor Configuration

- The processor must accept a `deployment_labels` map in its config (e.g., `{"env": "production", "region": "us-east-1", "version": "v2.3.1"}`)
- A `latency_threshold_ms` integer config field defines the threshold (default: 500ms) above which a span is flagged
- A `propagate_context` boolean config field controls whether deployment labels are injected into span context for downstream services
- The config must validate that `deployment_labels` is non-empty and `latency_threshold_ms` is positive

### Span Enrichment

- Every span passing through the processor must receive resource attributes from `deployment_labels` (e.g., `deployment.env`, `deployment.region`, `deployment.version`)
- If a span's duration exceeds `latency_threshold_ms`, the processor must add a `latency.anomaly` boolean attribute set to `true` and a `latency.exceeded_by_ms` integer attribute showing the overage
- Root spans (spans with no parent span ID) must receive an additional `trace.is_root` attribute set to `true`
- Spans with a `status.code` of ERROR must receive a `deployment.error_env` attribute combining the environment and service name (e.g., `production/payment-service`)

### File Trace Exporter

- The exporter writes one JSON object per span, newline-delimited, to a configurable output file path
- Each JSON object must include: `trace_id`, `span_id`, `parent_span_id`, `operation_name`, `service_name`, `start_time` (RFC 3339), `duration_ms`, `status_code`, `attributes` (flat key-value map)
- If the output file does not exist, the exporter must create it; if it exists, the exporter appends
- The exporter must flush writes after each batch to avoid data loss
- If the file path is invalid or unwritable, the exporter must return a permanent error (not retry)

### Pipeline Integration

- Both components must register with the Collector's component framework via their respective factory functions
- The processor must implement the `processor.Traces` interface from `go.opentelemetry.io/collector/processor`
- The exporter must implement the `exporter.Traces` interface from `go.opentelemetry.io/collector/exporter`
- Both must support the Collector's lifecycle methods: `Start(ctx, host)` and `Shutdown(ctx)`

### Expected Functionality

- A span with duration 750ms and `latency_threshold_ms=500` receives `latency.anomaly=true` and `latency.exceeded_by_ms=250`
- A span with duration 300ms and `latency_threshold_ms=500` does not receive any latency anomaly attributes
- A root span with empty parent span ID receives `trace.is_root=true`; a child span does not
- A span with status ERROR from service `auth-service` in env `staging` receives `deployment.error_env=staging/auth-service`
- The file exporter writes a span with trace_id `abc123`, operation `GET /users`, duration 42ms as a valid JSON line containing all required fields
- Exporting to a read-only file path returns a permanent error immediately without retrying
- An empty batch of spans results in no file writes and no errors

## Acceptance Criteria

- The deployment processor enriches every span with configured deployment labels as resource attributes
- Spans exceeding the latency threshold are flagged with `latency.anomaly` and `latency.exceeded_by_ms` attributes with correct values
- Root spans are identified and marked with `trace.is_root` regardless of latency
- Error spans include the combined `deployment.error_env` attribute
- The file exporter produces valid newline-delimited JSON with all required fields for each span
- The file exporter correctly handles file creation, appending, and write errors
- Both components pass `go vet` and unit tests covering normal operation, edge cases, and error paths
