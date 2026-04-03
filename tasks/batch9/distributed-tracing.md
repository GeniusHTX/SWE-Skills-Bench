# Task: Build an OpenTelemetry Collector Pipeline Configuration Generator

## Background

The OpenTelemetry Collector (https://github.com/open-telemetry/opentelemetry-collector) receives, processes, and exports telemetry data. A new Go package is needed that generates collector pipeline configurations (receivers, processors, exporters, pipelines) for common deployment patterns: a gateway collector with load balancing, tail-based sampling configuration, span-to-metrics derivation, and multi-tenant routing based on resource attributes.

## Files to Create/Modify

- `cmd/otelcol-gen/main.go` (create) — CLI that generates collector YAML configurations from deployment specification
- `internal/pipeline/receiver.go` (create) — Receiver configuration generators for OTLP (gRPC/HTTP), Jaeger, Zipkin, and Prometheus receivers
- `internal/pipeline/processor.go` (create) — Processor configuration generators: batch, memory_limiter, tail_sampling, span_metrics, attributes, resource, filter
- `internal/pipeline/exporter.go` (create) — Exporter configuration generators: OTLP, Jaeger, Prometheus, logging, and load-balancing exporter
- `internal/pipeline/builder.go` (create) — `PipelineBuilder` that composes receivers, processors, and exporters into complete collector configs with service pipelines
- `internal/pipeline/sampling.go` (create) — Tail-based sampling policy generator: rate limiting, string attribute, numeric attribute, status code, composite, and always_sample policies
- `internal/pipeline/builder_test.go` (create) — Unit tests for all generators and the pipeline builder

## Requirements

### Receiver Generators (`receiver.go`)

- Function `OTLPReceiver(grpcPort, httpPort int) ReceiverConfig`:
  - `otlp.protocols.grpc.endpoint: "0.0.0.0:<grpcPort>"`
  - `otlp.protocols.http.endpoint: "0.0.0.0:<httpPort>"`
  - Default ports: gRPC=4317, HTTP=4318
- Function `JaegerReceiver(thriftPort, grpcPort int) ReceiverConfig`:
  - `jaeger.protocols.thrift_http.endpoint`, `jaeger.protocols.grpc.endpoint`
- Function `PrometheusReceiver(scrapeConfigs []ScrapeConfig) ReceiverConfig`:
  - `prometheus.config.scrape_configs[]` with `job_name`, `scrape_interval`, `static_configs.targets`
- All receivers validate port range 1-65535

### Processor Generators (`processor.go`)

- Function `BatchProcessor(timeout string, sendBatchSize int) ProcessorConfig`:
  - `batch.timeout`, `batch.send_batch_size`, `batch.send_batch_max_size` (2x sendBatchSize)
- Function `MemoryLimiterProcessor(limitMiB, spikeLimitMiB int, checkInterval string) ProcessorConfig`:
  - `memory_limiter.limit_mib`, `memory_limiter.spike_limit_mib`, `memory_limiter.check_interval`
- Function `AttributesProcessor(actions []AttributeAction) ProcessorConfig`:
  - `attributes.actions[]` with `key`, `value`, `action` (insert/update/delete/upsert)
- Function `ResourceProcessor(attributes map[string]string) ProcessorConfig`:
  - Adds resource attributes to all telemetry data
- Function `FilterProcessor(spanFilter, metricFilter *FilterConfig) ProcessorConfig`:
  - `filter.spans.include/exclude` with `match_type` (regexp/strict) and `services`, `span_names`

### Exporter Generators (`exporter.go`)

- Function `OTLPExporter(endpoint string, insecure bool, headers map[string]string) ExporterConfig`:
  - `otlp.endpoint`, `otlp.tls.insecure`, `otlp.headers`
- Function `PrometheusExporter(port int, namespace string) ExporterConfig`:
  - `prometheus.endpoint: "0.0.0.0:<port>"`, `prometheus.namespace`
- Function `LoadBalancingExporter(backends []string, protocol string, routingKey string) ExporterConfig`:
  - `loadbalancing.routing_key` (one of: "traceID", "service")
  - `loadbalancing.protocol.otlp.endpoint` (template)
  - `loadbalancing.resolver.static.hostnames` — list of backend addresses
- Function `LoggingExporter(verbosity string) ExporterConfig`:
  - `logging.verbosity` (one of: "basic", "normal", "detailed")

### Pipeline Builder (`builder.go`)

- Struct `PipelineBuilder` with methods:
  - `AddReceiver(name string, config ReceiverConfig) *PipelineBuilder`
  - `AddProcessor(name string, config ProcessorConfig) *PipelineBuilder`
  - `AddExporter(name string, config ExporterConfig) *PipelineBuilder`
  - `AddPipeline(name string, signalType string, receivers, processors, exporters []string) *PipelineBuilder`
  - `Build() (CollectorConfig, error)`
- `CollectorConfig` struct: `Receivers`, `Processors`, `Exporters`, `Service.Pipelines`, `Service.Extensions`, `Service.Telemetry`
- `Build()` validates:
  - Every pipeline references only defined receivers/processors/exporters
  - Signal type is one of "traces", "metrics", "logs"
  - At least one pipeline is defined
  - Memory limiter is first processor in each pipeline (warning if not)
- Method `ToYAML() ([]byte, error)` — Marshals to YAML

### Tail Sampling (`sampling.go`)

- Function `TailSampling(policies []SamplingPolicy, decisionWait string, numTraces int) ProcessorConfig`:
  - `tail_sampling.decision_wait` (e.g., "10s")
  - `tail_sampling.num_traces` — buffer size
  - `tail_sampling.policies[]` from provided policies
- Policy generators:
  - `AlwaysSamplePolicy(name string)` — Always sample
  - `RateLimitingPolicy(name string, spansPerSecond int)` — Rate limiting
  - `StringAttributePolicy(name, key string, values []string)` — Match string attribute
  - `StatusCodePolicy(name string, codes []string)` — Match span status (ERROR, OK)
  - `CompositePolicy(name string, subPolicies []SamplingPolicy, rateAllocation []RateAllocation)` — Composite with rate allocation per sub-policy
- Each policy has `name` and `type` fields matching the collector's expected format

### Expected Functionality

- Building a gateway config with OTLP receiver (4317/4318), batch + memory_limiter processors, and load-balancing exporter to 3 backends produces valid YAML
- Tail sampling with rate limiting (100 spans/s) + status code (ERROR always sampled) produces correct composite policy
- Pipeline builder rejects a pipeline referencing undefined exporter "nonexistent"
- Generated YAML is valid and pasreable by `yaml.Unmarshal`

## Acceptance Criteria

- All receiver configurations include protocol-specific endpoints with validated ports
- Processor configurations match the collector's expected YAML schema
- Load-balancing exporter correctly configures routing key and static resolver
- Pipeline builder validates cross-references between components
- Tail sampling generates correct policy structures for all 5 policy types
- Memory limiter warning is emitted when it's not the first processor
- Generated configs marshal to valid YAML
- `python -m pytest /workspace/tests/test_distributed_tracing.py -v --tb=short` passes
