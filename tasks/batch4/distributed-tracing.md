# Task: Implement a Distributed Tracing Pipeline Configuration with Jaeger and OpenTelemetry Collector

## Background

The OpenTelemetry Collector repository (https://github.com/open-telemetry/opentelemetry-collector) is a vendor-agnostic proxy for telemetry data. A new example configuration is needed that sets up a complete distributed tracing pipeline: an OpenTelemetry Collector configuration receiving traces from multiple services via OTLP and Jaeger protocols, processing them with batching and attribute enrichment, exporting to Jaeger and Prometheus, plus a Docker Compose setup and Python instrumentation example demonstrating end-to-end trace propagation across three services.

## Files to Create/Modify

- `examples/tracing-demo/collector/otel-collector-config.yaml` (create) — OpenTelemetry Collector configuration with receivers, processors, and exporters
- `examples/tracing-demo/docker-compose.yaml` (create) — Docker Compose with Jaeger, OTel Collector, and three sample services
- `examples/tracing-demo/services/gateway/app.py` (create) — Python API gateway service instrumented with OpenTelemetry
- `examples/tracing-demo/services/user/app.py` (create) — Python user service instrumented with OpenTelemetry
- `examples/tracing-demo/services/order/app.py` (create) — Python order service instrumented with OpenTelemetry
- `examples/tracing-demo/services/tracing_config.py` (create) — Shared tracing initialization module
- `tests/test_distributed_tracing.py` (create) — Tests validating configuration structure and instrumentation correctness

## Requirements

### OpenTelemetry Collector Configuration

**Receivers:**
- `otlp`: gRPC on port 4317, HTTP on port 4318
- `jaeger`: gRPC on port 14250, thrift_http on port 14268

**Processors:**
- `batch`: send_batch_size 512, timeout 5s, send_batch_max_size 1024
- `attributes`: insert `environment: "demo"`, insert `collector.version: "1.0"`
- `memory_limiter`: check_interval 1s, limit_mib 512, spike_limit_mib 128

**Exporters:**
- `jaeger`: endpoint `jaeger:14250`, tls insecure
- `prometheus`: endpoint `0.0.0.0:8889`, namespace `otel`
- `logging`: loglevel `info`

**Service pipelines:**
- `traces`: receivers [otlp, jaeger], processors [memory_limiter, batch, attributes], exporters [jaeger, logging]
- `metrics`: receivers [otlp], processors [memory_limiter, batch], exporters [prometheus]

**Extensions:**
- `health_check`: endpoint `0.0.0.0:13133`
- `zpages`: endpoint `0.0.0.0:55679`

### Docker Compose

- `jaeger`: image `jaegertracing/all-in-one:latest`, ports 16686 (UI), 14250 (gRPC), 14268 (HTTP)
- `otel-collector`: image `otel/opentelemetry-collector-contrib:latest`, volumes mount config file, ports 4317, 4318, 8889, depends_on jaeger
- `gateway`: builds from `services/gateway/`, port 8080, environment `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317`, `SERVICE_NAME=gateway`, depends_on otel-collector
- `user-service`: builds from `services/user/`, port 8081, same OTLP endpoint, `SERVICE_NAME=user-service`
- `order-service`: builds from `services/order/`, port 8082, same OTLP endpoint, `SERVICE_NAME=order-service`

### Shared Tracing Configuration (tracing_config.py)

- `init_tracing(service_name: str, endpoint: str)` — initializes OpenTelemetry with:
  - `Resource` with `service.name` attribute
  - `OTLPSpanExporter` pointing to the collector gRPC endpoint
  - `BatchSpanProcessor` with the exporter
  - `TracerProvider` set as global
  - Flask or FastAPI auto-instrumentation
- `get_tracer(name: str)` — returns a tracer from the global provider
- Context propagation: `TraceContextTextMapPropagator` must be set as the global propagator for W3C Trace Context header (`traceparent`) propagation

### Service Instrumentation

**Gateway (`gateway/app.py`):**
- Flask app on port 8080
- `GET /api/users/{id}` — creates a span `"gateway.get_user"`, adds attributes `user.id`, calls user-service via HTTP (propagating trace context headers), returns result
- `POST /api/orders` — creates a span `"gateway.create_order"`, calls both user-service and order-service, combining results

**User Service (`user/app.py`):**
- Flask app on port 8081
- `GET /users/{id}` — creates a span `"user.get"`, simulates DB query with a child span `"db.query"` (attribute `db.system=postgresql`, `db.statement="SELECT * FROM users WHERE id=?"`)

**Order Service (`order/app.py`):**
- Flask app on port 8082
- `POST /orders` — creates a span `"order.create"`, simulates DB insert with child span `"db.insert"`, then calls user-service to verify user exists (propagating trace context)

### Trace Context Propagation

- All inter-service HTTP calls must inject the `traceparent` header via OpenTelemetry's propagator
- All services must extract the `traceparent` header from incoming requests
- A single request to the gateway must produce a trace spanning all three services with a common trace ID

### Expected Functionality

- `docker-compose up` starts Jaeger, OTel Collector, and three services
- A GET to `gateway:8080/api/users/1` produces a trace visible in Jaeger UI at `localhost:16686` with spans from gateway and user-service
- A POST to `gateway:8080/api/orders` produces a trace with spans from all three services
- The OTel Collector batches and enriches spans with the `environment` attribute before exporting to Jaeger
- Prometheus metrics from the collector are available at `localhost:8889/metrics`

## Acceptance Criteria

- OTel Collector config is valid YAML with correct receivers, processors, exporters, and pipeline definitions
- Docker Compose correctly wires all services with proper port mappings and dependencies
- All three services initialize tracing with the correct service name and OTLP endpoint
- Trace context propagation via `traceparent` header works across all inter-service HTTP calls
- Custom spans with attributes (db.system, db.statement, user.id) are created at each service
- The collector processes traces through memory_limiter, batch, and attributes processors in order
- Tests validate configuration structure, span attributes, and propagation header handling
