# Task: Configure Prometheus Monitoring for a Multi-Service E-Commerce Platform

## Background

A Kubernetes-based e-commerce platform with 5 microservices (product-catalog, cart, checkout, user-auth, recommendation-engine) needs comprehensive Prometheus monitoring. Each service exposes custom application metrics. The setup requires service discovery, relabeling, recording rules for pre-computed dashboards, and alerting rules for operational health. Node-level monitoring via node-exporter and a Redis exporter for the shared cache layer must also be configured.

## Files to Create/Modify

- `monitoring/prometheus/prometheus.yml` (create) — Main Prometheus configuration with global settings, scrape configs, service discovery, and relabeling rules
- `monitoring/prometheus/rules/recording-rules.yml` (create) — Recording rules for pre-computed RED metrics per service
- `monitoring/prometheus/rules/alerting-rules.yml` (create) — Alerting rules for service health, infrastructure, and business metrics
- `monitoring/prometheus/rules/node-alerts.yml` (create) — Node-level alerting rules for CPU, memory, disk, and network
- `monitoring/alertmanager/alertmanager.yml` (create) — Alertmanager configuration with routing, receivers (Slack, PagerDuty), inhibition, and silencing
- `monitoring/exporters/redis-exporter.yaml` (create) — Kubernetes Deployment and Service for redis_exporter scraping the shared Redis cluster

## Requirements

### Global Configuration (`monitoring/prometheus/prometheus.yml`)

- `scrape_interval: 15s`, `evaluation_interval: 15s`.
- External labels: `cluster: "production"`, `region: "us-east-1"`.
- Rule files: `/etc/prometheus/rules/*.yml`.
- Alertmanager target: `alertmanager.monitoring:9093`.

### Scrape Configs

**Job: `kubernetes-pods`**
- `kubernetes_sd_configs`: role `pod`.
- Relabel configs:
  - Keep pods with annotation `prometheus.io/scrape: "true"`.
  - Replace `__metrics_path__` from `prometheus.io/path` annotation (default `/metrics`).
  - Replace `__address__` with `prometheus.io/port` annotation.
  - Map `__meta_kubernetes_namespace` → label `namespace`.
  - Map `__meta_kubernetes_pod_name` → label `pod`.
  - Map `__meta_kubernetes_pod_label_app` → label `app`.
  - Map `__meta_kubernetes_pod_label_version` → label `version`.
- Metric relabel: drop metrics matching `go_.*` and `promhttp_.*` (reduce cardinality).

**Job: `kubernetes-services`**
- `kubernetes_sd_configs`: role `service`.
- Keep services with annotation `prometheus.io/scrape: "true"`.
- Relabel namespace and service name.

**Job: `node-exporter`**
- `kubernetes_sd_configs`: role `node`.
- Relabel `__address__` to port 9100 on each node.
- Map `__meta_kubernetes_node_name` → label `node`.
- Map `__meta_kubernetes_node_label_topology_kubernetes_io_zone` → label `zone`.

**Job: `redis-exporter`**
- `static_configs`: target `redis-exporter.monitoring:9121`.
- Labels: `service: "redis-cache"`.

**Job: `kube-state-metrics`**
- Target: `kube-state-metrics.monitoring:8080`.

### Recording Rules (`monitoring/prometheus/rules/recording-rules.yml`)

Group `service_red_metrics` (interval 30s):

```yaml
# Request rate per service (5m window)
- record: service:http_requests:rate5m
  expr: sum(rate(http_requests_total[5m])) by (app, namespace)

# Error rate per service
- record: service:http_errors:ratio_rate5m
  expr: |
    sum(rate(http_requests_total{status=~"5.."}[5m])) by (app, namespace)
    / sum(rate(http_requests_total[5m])) by (app, namespace)

# P50 latency per service
- record: service:http_duration:p50_5m
  expr: histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, app, namespace))

# P95 latency per service
- record: service:http_duration:p95_5m
  expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, app, namespace))

# P99 latency per service
- record: service:http_duration:p99_5m
  expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, app, namespace))
```

Group `infra_metrics`:

```yaml
# Node CPU utilization
- record: node:cpu_utilization:ratio
  expr: 1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (node)

# Node memory utilization
- record: node:memory_utilization:ratio
  expr: |
    1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

# Redis connected clients
- record: redis:connected_clients:current
  expr: redis_connected_clients

# Redis memory usage ratio
- record: redis:memory_usage:ratio
  expr: redis_memory_used_bytes / redis_memory_max_bytes
```

### Alerting Rules (`monitoring/prometheus/rules/alerting-rules.yml`)

Group `service_alerts`:

- `ServiceHighErrorRate`: `service:http_errors:ratio_rate5m > 0.05` for 5m. Severity: `critical`. Summary: `"{{ $labels.app }} error rate is {{ $value | humanizePercentage }}"`.
- `ServiceHighLatencyP95`: `service:http_duration:p95_5m > 1.0` for 5m. Severity: `warning`.
- `ServiceHighLatencyP99`: `service:http_duration:p99_5m > 3.0` for 5m. Severity: `critical`.
- `ServiceDown`: `up{job="kubernetes-pods"} == 0` for 2m. Severity: `critical`.
- `CheckoutServiceSlowdown`: `service:http_duration:p95_5m{app="checkout"} > 0.5` for 3m. Severity: `critical`. (Checkout must be fast.)

Group `redis_alerts`:

- `RedisHighMemory`: `redis:memory_usage:ratio > 0.85` for 5m. Severity: `warning`.
- `RedisHighMemoryCritical`: `redis:memory_usage:ratio > 0.95` for 2m. Severity: `critical`.
- `RedisTooManyConnections`: `redis_connected_clients > 500` for 5m. Severity: `warning`.
- `RedisDown`: `up{job="redis-exporter"} == 0` for 1m. Severity: `critical`.

### Node-Level Alerts (`monitoring/prometheus/rules/node-alerts.yml`)

- `NodeHighCPU`: `node:cpu_utilization:ratio > 0.85` for 10m. Severity: `warning`.
- `NodeHighMemory`: `node:memory_utilization:ratio > 0.90` for 5m. Severity: `warning`.
- `NodeDiskSpaceLow`: `(node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.15` for 5m. Severity: `warning`.
- `NodeDiskSpaceCritical`: same but `< 0.05` for 2m. Severity: `critical`.
- `NodeNetworkErrors`: `rate(node_network_receive_errs_total[5m]) + rate(node_network_transmit_errs_total[5m]) > 10` for 5m. Severity: `warning`.

### Alertmanager (`monitoring/alertmanager/alertmanager.yml`)

- Global: `resolve_timeout: 5m`, `smtp_smarthost: "smtp.example.com:587"`, `smtp_from: "alerts@example.com"`.
- Route tree:
  - Default receiver: `slack-warnings`.
  - `severity: critical` → receiver `pagerduty-critical`, `group_wait: 10s`, `repeat_interval: 1h`.
  - `severity: critical` + `app: checkout` → receiver `pagerduty-checkout-oncall`, `group_wait: 5s` (checkout has separate on-call).
  - `severity: warning` → receiver `slack-warnings`, `repeat_interval: 4h`.
- Receivers:
  - `pagerduty-critical`: PagerDuty with `service_key: <PAGERDUTY_SERVICE_KEY>`.
  - `pagerduty-checkout-oncall`: PagerDuty with `service_key: <CHECKOUT_PAGERDUTY_KEY>`.
  - `slack-warnings`: Slack webhook to `#monitoring-warnings` channel.
- Inhibition rules:
  - `ServiceDown` inhibits `ServiceHighErrorRate` and `ServiceHighLatencyP95` for same `app` label (if entire service is down, suppress symptom alerts).
  - `NodeHighMemory` where severity=`critical` inhibits severity=`warning` for same `node`.

### Redis Exporter (`monitoring/exporters/redis-exporter.yaml`)

- Deployment: image `oliver006/redis_exporter:v1.58.0`, 1 replica.
- Environment variable: `REDIS_ADDR=redis-cluster.cache:6379`.
- Service: ClusterIP port 9121, annotation `prometheus.io/scrape: "true"`, `prometheus.io/port: "9121"`.
- Resources: requests `cpu: 50m, memory: 64Mi`, limits `cpu: 100m, memory: 128Mi`.

### Expected Functionality

- Prometheus discovers all annotated pods in Kubernetes and scrapes `/metrics` on configured port.
- Recording rules compute RED metrics (rate, errors, duration) per service every 30 seconds.
- `checkout` P95 latency exceeds 500ms for 3 minutes → `CheckoutServiceSlowdown` alert → Alertmanager routes to PagerDuty checkout on-call.
- Redis memory reaches 90% → `RedisHighMemory` warning → Slack notification.
- A node goes down → `ServiceDown` fires → inhibits redundant `ServiceHighErrorRate` for services on that node.

## Acceptance Criteria

- Prometheus config uses `kubernetes_sd_configs` for pod, service, and node discovery with annotation-based filtering.
- Metric relabeling drops high-cardinality `go_*` and `promhttp_*` metrics.
- Recording rules pre-compute request rate, error ratio, P50/P95/P99 latency grouped by app and namespace.
- Alerting rules cover service-level (error rate, latency, downtime), infrastructure-level (CPU, memory, disk, network), and dependency-level (Redis) health.
- Checkout service has a stricter latency threshold (500ms) than other services (1s).
- Alertmanager routes critical alerts to PagerDuty and warnings to Slack with appropriate group_wait and repeat_interval settings.
- Checkout-specific critical alerts route to a dedicated PagerDuty rotation.
- Inhibition rules suppress symptom alerts when root cause alerts are already firing.
- Redis exporter Deployment has Prometheus scrape annotations, resource limits, and targets the Redis cluster address.
