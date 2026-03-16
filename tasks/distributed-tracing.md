# Task: Add OpenTelemetry Collector Pipeline Configuration Example

## Background
   Add a complete collector pipeline
   configuration example demonstrating receivers, processors, and exporters
   in the OpenTelemetry Collector repository.

## Files to Create/Modify
   - examples/pipeline-demo/config.yaml (collector configuration)
   - examples/pipeline-demo/README.md (documentation)
   - examples/pipeline-demo/docker-compose.yaml (optional local setup)

## Requirements
   
   Collector Configuration (config.yaml):
   
   Receivers:
   - otlp: gRPC and HTTP protocols
   - prometheus: Prometheus scrape endpoint
   - jaeger: Jaeger thrift receiver
   
   Processors:
   - batch: Batch telemetry data
   - memory_limiter: Limit memory usage
   - attributes: Add/modify span attributes
   - filter: Drop unwanted telemetry
   
   Exporters:
   - otlp: Send to OTLP endpoint
   - prometheus: Expose Prometheus endpoint
   - logging: Debug output
   
   Pipelines:
   - traces: otlp -> batch -> otlp
   - metrics: prometheus -> memory_limiter -> prometheus
   - logs: otlp -> filter -> logging

4. Configuration Features:
   - Multi-pipeline setup
   - Batch configuration tuning
   - Memory limits for production
   - TLS configuration placeholders

## Acceptance Criteria
   - `otelcol validate --config examples/pipeline-demo/config.yaml` exits with code 0
   - All receivers, processors, exporters properly configured
   - README explains each pipeline component
