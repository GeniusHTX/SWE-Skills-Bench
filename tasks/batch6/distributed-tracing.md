# Task: Implement Distributed Tracing for a Python Microservices Application Using OpenTelemetry and Jaeger

## Background

A Python microservices application with 4 services (api-gateway, user-service, order-service, notification-service) needs distributed tracing using OpenTelemetry SDK and Jaeger as the backend. Each service must propagate trace context, create meaningful spans with attributes, and export traces to a Jaeger collector. The setup includes a Docker Compose environment for local development and Kubernetes manifests for production.

## Files to Create/Modify

- `lib/tracing/__init__.py` (create) — Shared tracing library: `init_tracer(service_name)` function that configures OpenTelemetry with Jaeger exporter
- `lib/tracing/middleware.py` (create) — FastAPI middleware that creates request spans with standard HTTP attributes
- `lib/tracing/propagation.py` (create) — Helper for propagating trace context in outgoing HTTP requests (inject W3C traceparent headers)
- `services/api-gateway/tracing_setup.py` (create) — Initialize tracing for api-gateway, instrument FastAPI and httpx
- `services/user-service/tracing_setup.py` (create) — Initialize tracing for user-service, instrument FastAPI and SQLAlchemy
- `services/order-service/tracing_setup.py` (create) — Initialize tracing for order-service, instrument FastAPI, httpx, and SQLAlchemy
- `services/notification-service/tracing_setup.py` (create) — Initialize tracing for notification-service, instrument FastAPI and Celery
- `docker-compose.tracing.yml` (create) — Docker Compose overlay adding Jaeger all-in-one, OpenTelemetry Collector, and tracing env vars
- `k8s/tracing/jaeger.yaml` (create) — Jaeger Kubernetes Deployment using jaeger-operator with production storage (Elasticsearch)
- `k8s/tracing/otel-collector.yaml` (create) — OpenTelemetry Collector Deployment with receivers, processors, and Jaeger exporter

## Requirements

### Shared Tracing Library (`lib/tracing/__init__.py`)

- `init_tracer(service_name: str, jaeger_endpoint: str = None) -> TracerProvider`:
  - Create `Resource` with `service.name`, `service.version`, `deployment.environment` attributes.
  - Configure `TracerProvider` with the resource.
  - Add `BatchSpanProcessor` with `OTLPSpanExporter` pointing to `jaeger_endpoint` (default from `OTEL_EXPORTER_OTLP_ENDPOINT` env var, fallback `http://localhost:4317`).
  - Set the global tracer provider via `trace.set_tracer_provider()`.
  - Return the provider for testing purposes.
- `get_tracer(name: str) -> Tracer` — convenience wrapper for `trace.get_tracer(name)`.

### Tracing Middleware (`lib/tracing/middleware.py`)

- FastAPI middleware class `TracingMiddleware`:
  - Creates a span for every HTTP request with name `"{method} {path}"`.
  - Sets span attributes: `http.method`, `http.url`, `http.route`, `http.status_code`, `http.request_content_length`, `net.peer.ip`, `user_agent.original`.
  - Sets span status to `ERROR` if status code >= 500.
  - Adds exception event to span if request handler raises (captures exception type, message, stacktrace).
  - Injects `X-Request-ID` response header from span's trace ID.

### Context Propagation (`lib/tracing/propagation.py`)

- `inject_trace_context(headers: dict) -> dict` — injects W3C `traceparent` and `tracestate` headers into an outgoing request headers dict.
- `traced_http_call(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> httpx.Response`:
  - Creates a child span named `"HTTP {method} {parsed_host}{path}"`.
  - Injects trace context into request headers.
  - Sets span attributes: `http.method`, `http.url`, `http.status_code`.
  - Records error if response status >= 400.
  - Returns response.

### Service Instrumentation

Each service's `tracing_setup.py` must:
1. Call `init_tracer(service_name="<name>")`.
2. Apply auto-instrumentation for the relevant libraries:
   - **api-gateway**: `FastAPIInstrumentor`, `HTTPXClientInstrumentor`
   - **user-service**: `FastAPIInstrumentor`, `SQLAlchemyInstrumentor`
   - **order-service**: `FastAPIInstrumentor`, `HTTPXClientInstrumentor`, `SQLAlchemyInstrumentor`
   - **notification-service**: `FastAPIInstrumentor`, `CeleryInstrumentor`
3. Add custom spans for business operations:
   - **order-service**: `create_order` function creates span `"order.create"` with attributes `order.id`, `order.total`, `order.items_count`.
   - **user-service**: `lookup_user` creates span `"user.lookup"` with attributes `user.id`, `user.email_domain`.
   - **notification-service**: `send_notification` creates span `"notification.send"` with attributes `notification.type`, `notification.channel`, `notification.recipient_count`.

### Docker Compose (`docker-compose.tracing.yml`)

- Services:
  - `jaeger`: image `jaegertracing/all-in-one:1.53`, ports: 16686 (UI), 14268 (HTTP collector), 4317 (OTLP gRPC), 4318 (OTLP HTTP).
  - `otel-collector`: image `otel/opentelemetry-collector-contrib:0.96.0`, config from volume mount, ports: 4317 (gRPC), 4318 (HTTP), 8888 (metrics).
- Environment variables for each application service:
  - `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317`
  - `OTEL_SERVICE_NAME=<service-name>`
  - `OTEL_RESOURCE_ATTRIBUTES=deployment.environment=development`

### OpenTelemetry Collector Config (embedded in `docker-compose.tracing.yml` or separate file)

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 5s
    send_batch_size: 512
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 128

exporters:
  otlp/jaeger:
    endpoint: jaeger:4317
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/jaeger]
```

### Kubernetes Jaeger (`k8s/tracing/jaeger.yaml`)

- Jaeger CRD: `apiVersion: jaegertracing.io/v1`, kind `Jaeger`.
- Strategy: `production` (not all-in-one).
- Storage: `type: elasticsearch`, `server-urls: http://elasticsearch.observability:9200`.
- Collector replicas: 2.
- Query (UI) with ingress at `jaeger.internal.example.com`.

### Kubernetes OTel Collector (`k8s/tracing/otel-collector.yaml`)

- Deployment with 2 replicas.
- ConfigMap with receiver/processor/exporter config same as above but exporting to the Jaeger collector service.
- Service: ClusterIP ports 4317, 4318.
- Resource limits: `cpu: 500m, memory: 512Mi`.

### Expected Functionality

- User sends `POST /api/orders` to api-gateway → trace spans: `gateway.POST /api/orders` → `order-service.create_order` → `user-service.lookup_user` → `notification-service.send_notification` → all visible as one trace in Jaeger UI.
- Opening Jaeger UI at `http://localhost:16686` → search by service `order-service` → shows traces with correct parent-child span relationships.
- A 500 error in user-service → span has `ERROR` status with exception event containing stacktrace, visible upstream in the gateway span.
- Each span has standard HTTP semantic convention attributes (`http.method`, `http.status_code`, `http.url`).

## Acceptance Criteria

- `init_tracer` configures OpenTelemetry with OTLP exporter targeting the configured endpoint and sets service resource attributes.
- Tracing middleware creates per-request spans with HTTP semantic convention attributes.
- Context propagation injects W3C `traceparent` headers in outgoing HTTP calls, maintaining trace continuity across services.
- Each service auto-instruments its specific libraries (FastAPI, httpx, SQLAlchemy, Celery).
- Custom business spans include domain-specific attributes (order.id, notification.type, etc.).
- Docker Compose includes Jaeger all-in-one and OTel Collector with OTLP receiver, batch processor, and Jaeger exporter.
- Kubernetes manifests deploy Jaeger in production mode with Elasticsearch storage and OTel Collector with 2 replicas.
- Error spans include exception events with type, message, and stacktrace.
- All services share the same tracing library for consistent configuration and instrumentation.
