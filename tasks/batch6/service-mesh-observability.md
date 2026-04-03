# Task: Build a Service Mesh Observability Stack with Golden Signal Dashboards

## Background

A Kubernetes-based microservices platform running Istio service mesh needs a complete observability stack: Prometheus for metrics collection, Grafana dashboards for visualization, Jaeger for distributed traces, and Kiali for service graph. The stack must monitor the four golden signals (latency, traffic, errors, saturation) for all meshed services, with alerting rules for SLO violations.

## Files to Create/Modify

- `observability/prometheus/config.yaml` (create) — Prometheus ConfigMap with Istio metric scrape configs and recording rules
- `observability/prometheus/alerts.yaml` (create) — PrometheusRule with alerting rules for golden signal thresholds
- `observability/grafana/dashboards/mesh-overview.json` (create) — Grafana dashboard JSON: service mesh overview with golden signals for all services
- `observability/grafana/dashboards/service-detail.json` (create) — Grafana dashboard JSON: single-service deep dive with per-route metrics
- `observability/grafana/datasources.yaml` (create) — Grafana datasource provisioning for Prometheus and Jaeger
- `observability/kiali/kiali-cr.yaml` (create) — Kiali custom resource for service graph visualization
- `observability/otel-collector/config.yaml` (create) — OpenTelemetry Collector config receiving Istio telemetry and exporting to Prometheus + Jaeger

## Requirements

### Prometheus Configuration (`observability/prometheus/config.yaml`)

- Scrape configs:
  - `istio-mesh` job: scrape `istio-telemetry` in `istio-system` namespace, interval 15s.
  - `envoy-stats` job: scrape Envoy sidecar metrics from all meshed pods via `kubernetes_sd_configs` role `pod`, relabel to filter pods with `sidecar.istio.io/status` annotation, scrape port 15090 path `/stats/prometheus`.
  - `istiod` job: scrape istiod control plane metrics.
  - `kubernetes-pods` job: scrape application-level metrics from pods with `prometheus.io/scrape: "true"` annotation.

- Recording rules (for performance, pre-compute expensive queries):
  ```yaml
  groups:
    - name: istio_sli_rules
      interval: 30s
      rules:
        - record: sli:istio_request_rate:5m
          expr: sum(rate(istio_requests_total{reporter="destination"}[5m])) by (destination_service_name, destination_workload_namespace)

        - record: sli:istio_error_rate:5m
          expr: |
            sum(rate(istio_requests_total{reporter="destination", response_code=~"5.."}[5m])) by (destination_service_name)
            / sum(rate(istio_requests_total{reporter="destination"}[5m])) by (destination_service_name)

        - record: sli:istio_latency_p50:5m
          expr: histogram_quantile(0.50, sum(rate(istio_request_duration_milliseconds_bucket{reporter="destination"}[5m])) by (le, destination_service_name))

        - record: sli:istio_latency_p99:5m
          expr: histogram_quantile(0.99, sum(rate(istio_request_duration_milliseconds_bucket{reporter="destination"}[5m])) by (le, destination_service_name))

        - record: sli:istio_tcp_connections:current
          expr: sum(istio_tcp_connections_opened_total{reporter="destination"}) by (destination_service_name) - sum(istio_tcp_connections_closed_total{reporter="destination"}) by (destination_service_name)
  ```

### Alerting Rules (`observability/prometheus/alerts.yaml`)

- `apiVersion: monitoring.coreos.com/v1`, kind `PrometheusRule`.
- Alert groups:

  **Group: mesh-golden-signals**
  - `HighErrorRate`: `sli:istio_error_rate:5m > 0.01` for 5 minutes. Severity: `critical`. Annotations: summary `"{{ $labels.destination_service_name }} error rate is {{ $value | humanizePercentage }}"`.
  - `HighLatencyP99`: `sli:istio_latency_p99:5m > 500` for 5 minutes. Severity: `warning`. Summary: P99 latency exceeds 500ms.
  - `HighLatencyP99Critical`: `sli:istio_latency_p99:5m > 2000` for 2 minutes. Severity: `critical`. P99 > 2 seconds.
  - `LowTraffic`: `sli:istio_request_rate:5m < 1` for 10 minutes during business hours (using `day_of_week()` and `hour()` functions). Severity: `warning`. Summary: Unexpected low traffic.
  - `HighSaturation`: `container_memory_working_set_bytes / container_spec_memory_limit_bytes > 0.85` for 5 minutes. Severity: `warning`.

  **Group: mesh-connectivity**
  - `ServiceUnreachable`: `istio_requests_total{response_code="503", response_flags="UH"} > 0` for 1 minute. Severity: `critical`. Summary: Upstream host unreachable.
  - `CircuitBreakerTripped`: `istio_requests_total{response_flags="UO"} > 0` for 1 minute. Severity: `warning`. Summary: Circuit breaker tripped.

### Grafana Dashboard — Mesh Overview (`observability/grafana/dashboards/mesh-overview.json`)

- Dashboard title: `"Service Mesh Overview"`, uid: `"mesh-overview"`.
- Template variable: `$namespace` (multi-select, query all namespaces from Prometheus).
- Rows:
  1. **Golden Signals Summary** (4 panels in a row):
     - **Request Rate**: timeseries panel, query `sli:istio_request_rate:5m{destination_workload_namespace=~"$namespace"}`, grouped by `destination_service_name`.
     - **Error Rate**: timeseries with threshold at 1% (red line), query `sli:istio_error_rate:5m * 100`.
     - **P50 Latency**: timeseries, query `sli:istio_latency_p50:5m`.
     - **P99 Latency**: timeseries with threshold at 500ms, query `sli:istio_latency_p99:5m`.
  2. **Service Table** (1 panel):
     - Table panel showing per-service: name, request rate, error rate, p50 latency, p99 latency, active connections.
     - Color-coded: error rate cells red if >1%, yellow if >0.1%.
  3. **Error Breakdown** (2 panels):
     - **Errors by Service**: bar chart, `sum(rate(istio_requests_total{response_code=~"5.."}[5m])) by (destination_service_name)`.
     - **Errors by Response Code**: pie chart, `sum(rate(istio_requests_total{response_code=~"[45].."}[5m])) by (response_code)`.
  4. **TCP Connections** (1 panel):
     - Timeseries: `sli:istio_tcp_connections:current` by service.

### Grafana Dashboard — Service Detail (`observability/grafana/dashboards/service-detail.json`)

- Dashboard title: `"Service Detail"`, uid: `"service-detail"`.
- Template variables: `$namespace`, `$service` (dependent on namespace).
- Rows:
  1. **Overview stats** (4 stat panels): current RPS, error rate %, P50 ms, P99 ms for the selected service.
  2. **Per-Route Metrics** (2 panels):
     - Request rate by `request_path` (requires Istio telemetry collecting path dimension).
     - Latency by `request_path`.
  3. **Client-Server Breakdown** (2 panels):
     - Inbound: traffic sources → this service (query `source_workload_name`).
     - Outbound: this service → destinations (query `destination_service_name` with `source_workload_name=~"$service"`).
  4. **Trace Integration** (1 panel):
     - Traces panel using Jaeger datasource, linked to service name, showing recent traces.

### Grafana Datasources (`observability/grafana/datasources.yaml`)

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus.observability:9090
    isDefault: true
    jsonData:
      timeInterval: 15s
  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger-query.observability:16686
    jsonData:
      tracesToMetrics:
        datasourceUid: prometheus
        tags: [{ key: "service.name", value: "destination_service_name" }]
  - name: Loki
    type: loki
    access: proxy
    url: http://loki.observability:3100
```

### Kiali Configuration (`observability/kiali/kiali-cr.yaml`)

- `apiVersion: kiali.io/v1alpha1`, kind `Kiali`.
- Namespace: `istio-system`.
- External services: Prometheus at `http://prometheus.observability:9090`, Grafana at `http://grafana.observability:3000`, Jaeger at `http://jaeger-query.observability:16686`.
- Auth strategy: `token`.
- Deployment: replicas 1, accessible via Ingress at `kiali.internal.example.com`.

### Expected Functionality

- Prometheus scrapes Istio metrics every 15s and computes golden signal recording rules every 30s.
- Grafana Mesh Overview shows request rate, error rate, P50/P99 latency for all services, filterable by namespace.
- Error rate exceeding 1% for 5 minutes → `HighErrorRate` alert fires with service name and percentage.
- Grafana Service Detail dashboard drills into a specific service showing per-route metrics and linked Jaeger traces.
- Kiali displays service graph with traffic flow, error rates, and version labels from Istio telemetry.

## Acceptance Criteria

- Prometheus scrape configs collect Istio mesh metrics, Envoy sidecar stats, istiod metrics, and pod application metrics.
- Recording rules pre-compute request rate, error rate, P50/P99 latency, and TCP connection count per service.
- Alerting rules fire on: error rate >1% (critical), P99 >500ms (warning) / >2000ms (critical), low traffic during business hours, high memory saturation >85%, upstream unreachable (503+UH), circuit breaker tripped (UO flag).
- Mesh Overview dashboard has 4 golden signal timeseries panels, a per-service summary table, error breakdown charts, and TCP connection panel.
- Service Detail dashboard supports namespace and service variable selectors with per-route metric panels and Jaeger trace integration.
- Grafana datasource provisioning configures Prometheus (default), Jaeger (with traces-to-metrics linking), and Loki.
- Kiali CR connects to Prometheus, Grafana, and Jaeger for integrated service graph visualization.
