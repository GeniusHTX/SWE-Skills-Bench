# Task: Build an OpenTelemetry Collector Pipeline for Distributed Tracing

## Background

The OpenTelemetry Collector (https://github.com/open-telemetry/opentelemetry-collector) receives, processes, and exports telemetry data. This task requires implementing a custom processor in Go that enriches trace spans with service dependency metadata and a complete collector configuration that receives traces via OTLP, processes them through the custom processor and standard processors, and exports to multiple backends.

## Files to Create/Modify

- `processor/dependencyprocessor/processor.go` (create) — Custom `dependencyProcessor` that analyzes incoming trace spans to extract service-to-service call relationships. For each span with a `peer.service` or `net.peer.name` attribute, it adds a `service.dependency` attribute recording the caller→callee relationship.
- `processor/dependencyprocessor/config.go` (create) — Configuration struct for the processor: `cache_ttl` (duration for caching known dependencies), `max_cache_size` (int), and `attribute_key` (customizable output attribute name, default `service.dependency`).
- `processor/dependencyprocessor/factory.go` (create) — Component factory implementing `processor.Factory` with `NewFactory()`, creating the processor from config.
- `processor/dependencyprocessor/processor_test.go` (create) — Unit tests for the processor with mock spans.
- `examples/tracing-pipeline/otel-collector-config.yaml` (create) — Collector configuration with: OTLP gRPC/HTTP receivers, batch processor, the dependency processor, memory limiter, and exporters to Jaeger (OTLP), Prometheus (for span metrics), and a debug exporter.
- `tests/test_distributed_tracing.py` (create) — Integration test validating collector config structure and processor behavior.

## Requirements

### Dependency Processor

- Implements `processor.Traces` interface with `processTraces(ctx, td pdata.Traces) (pdata.Traces, error)`.
- For each span in the trace data:
  - Extract the calling service name from the span's `Resource` attributes (`service.name`).
  - Extract the callee from span attributes: check `peer.service` first, then `net.peer.name` + `net.peer.port`, then `http.url` (extract host).
  - If a callee is identified, add attribute `service.dependency` = `"{caller} -> {callee}"` to the span.
  - Cache the dependency pair (caller, callee) in an LRU cache to avoid recomputation. If already cached, skip attribute addition (the attribute might already exist).
- Handle missing attributes gracefully — if no callee can be determined, skip the span without error.

### Configuration

```go
type Config struct {
    CacheTTL     time.Duration `mapstructure:"cache_ttl"`
    MaxCacheSize int           `mapstructure:"max_cache_size"`
    AttributeKey string        `mapstructure:"attribute_key"`
}
```
- Defaults: `cache_ttl: 5m`, `max_cache_size: 10000`, `attribute_key: service.dependency`.
- Validate: `cache_ttl > 0`, `max_cache_size > 0`, `attribute_key` non-empty.

### Factory

- `NewFactory()` returns a `processor.Factory` with type `"dependency"`.
- `createDefaultConfig()` returns config with default values.
- `createTracesProcessor(ctx, set, cfg, next)` instantiates the processor.

### Collector Configuration

- **Receivers**: `otlp` with gRPC (port 4317) and HTTP (port 4318).
- **Processors** (in pipeline order):
  1. `memory_limiter`: check interval 1s, limit 512MiB, spike limit 128MiB.
  2. `dependency`: default config.
  3. `batch`: send batch size 1024, timeout 5s.
- **Exporters**:
  - `otlp/jaeger`: endpoint `jaeger:4317`, TLS insecure.
  - `prometheus`: endpoint `0.0.0.0:8889`, namespace `otel`.
  - `debug`: verbosity `detailed`.
- **Service pipelines**:
  - `traces`: receivers [otlp], processors [memory_limiter, dependency, batch], exporters [otlp/jaeger, debug].
  - `metrics`: receivers [otlp], processors [memory_limiter, batch], exporters [prometheus].

### Expected Functionality

- A span from `order-service` calling `payment-service` (attribute `peer.service: payment-service`) → processor adds `service.dependency: "order-service -> payment-service"`.
- A span from `api-gateway` with `http.url: http://user-service:8080/users` → processor extracts `user-service` and adds `service.dependency: "api-gateway -> user-service"`.
- A span with no peer attributes → no `service.dependency` attribute added, no error.

## Acceptance Criteria

- The processor compiles with `go build ./processor/dependencyprocessor/...`.
- `processTraces` correctly extracts caller/callee pairs from `peer.service`, `net.peer.name`, and `http.url` attributes.
- The LRU cache limits memory usage to `max_cache_size` entries.
- Configuration validation rejects invalid values.
- Collector config is valid YAML with correct receiver/processor/exporter/pipeline structure.
- Tests verify span attribute injection for each caller identification method and the no-callee edge case.
