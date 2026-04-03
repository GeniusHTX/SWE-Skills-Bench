# Task: Add Service Discovery and Alerting Rules for a Kubernetes Monitoring Stack in Prometheus

## Background

Prometheus (https://github.com/prometheus/prometheus) is an open-source monitoring and alerting toolkit. The task is to create a production-grade Prometheus configuration that monitors a Kubernetes cluster, including service discovery for pods and nodes, recording rules for pre-computed metrics, and alerting rules for SLA-critical conditions — all within the Prometheus repository's documentation/examples directory structure.

## Files to Create/Modify

- `documentation/examples/k8s-monitoring/prometheus.yml` (create) — Main Prometheus configuration with Kubernetes service discovery, scrape configs for node-exporter, kube-state-metrics, and application pods
- `documentation/examples/k8s-monitoring/recording_rules.yml` (create) — Recording rules for pre-computed aggregate metrics (request rate, error rate, latency percentiles)
- `documentation/examples/k8s-monitoring/alerting_rules.yml` (create) — Alerting rules for high error rate, high latency, pod restarts, node pressure, and disk usage
- `documentation/examples/k8s-monitoring/alertmanager.yml` (create) — Alertmanager configuration with routing, grouping, inhibition, and a webhook receiver

## Requirements

### Prometheus Scrape Configuration (`prometheus.yml`)

- `global` section: `scrape_interval: 15s`, `evaluation_interval: 15s`, `scrape_timeout: 10s`
- External labels: `cluster: "production"`, `environment: "prod"`
- Rule files: reference both `recording_rules.yml` and `alerting_rules.yml`
- Alertmanager target: `alertmanager:9093`

#### Scrape Jobs

- **`kubernetes-nodes`**: Use `kubernetes_sd_configs` with `role: node`; relabel `__address__` to use the Kubelet metrics endpoint on port 10250; add `__metrics_path__` = `/metrics`; keep label `node`
- **`kubernetes-pods`**: Use `kubernetes_sd_configs` with `role: pod`; only scrape pods with annotation `prometheus.io/scrape: "true"`; read port from `prometheus.io/port` annotation; read path from `prometheus.io/path` annotation (default `/metrics`)
- **`kube-state-metrics`**: Static target `kube-state-metrics:8080` in `kube-system` namespace
- **`node-exporter`**: Use `kubernetes_sd_configs` with `role: node`; relabel to target port 9100
- Each job must include appropriate `metric_relabel_configs` to drop high-cardinality metrics (e.g., `go_gc_*` metrics if label cardinality exceeds threshold)

### Recording Rules (`recording_rules.yml`)

- Group name: `k8s_aggregations`, evaluation interval: `15s`
- `namespace_http_request_rate_5m`: `sum(rate(http_requests_total[5m])) by (namespace, service, method, code)`
- `namespace_http_error_rate_5m`: `sum(rate(http_requests_total{code=~"5.."}[5m])) by (namespace, service)` / `sum(rate(http_requests_total[5m])) by (namespace, service)`
- `namespace_http_latency_p99_5m`: `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (namespace, service, le))`
- `namespace_http_latency_p50_5m`: `histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (namespace, service, le))`
- `node_cpu_utilization`: `1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)`
- `node_memory_utilization`: `1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)`

### Alerting Rules (`alerting_rules.yml`)

- Group name: `k8s_alerts`

#### Alert Definitions

- **`HighErrorRate`**: fires when `namespace_http_error_rate_5m > 0.05` for 5 minutes; severity: `critical`; annotations must include `summary` and `description` with `{{ $labels.namespace }}` and `{{ $labels.service }}`
- **`HighLatencyP99`**: fires when `namespace_http_latency_p99_5m > 1.0` (1 second) for 10 minutes; severity: `warning`
- **`PodCrashLooping`**: fires when `increase(kube_pod_container_status_restarts_total[1h]) > 5`; severity: `critical`; annotations must include the pod name
- **`NodeHighCPU`**: fires when `node_cpu_utilization > 0.85` for 15 minutes; severity: `warning`
- **`NodeDiskPressure`**: fires when `(node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.10` for the root filesystem; severity: `critical`
- **`KubeDeploymentReplicasMismatch`**: fires when `kube_deployment_status_replicas_available != kube_deployment_spec_replicas` for 15 minutes; severity: `warning`

### Alertmanager Configuration (`alertmanager.yml`)

- Route tree: group by `[namespace, alertname]`, `group_wait: 30s`, `group_interval: 5m`, `repeat_interval: 4h`
- Default receiver: `webhook-notifications`
- Sub-route for `severity: critical` alerts: receiver `pagerduty-critical`, `repeat_interval: 1h`
- Inhibition rule: if `HighErrorRate` is firing for a service, suppress `HighLatencyP99` for the same service/namespace
- Webhook receiver: send to `http://alert-receiver:9095/webhook`

## Expected Functionality

- Prometheus loads the configuration without errors and discovers Kubernetes nodes and annotated pods
- Recording rules produce pre-computed metrics visible in the Prometheus expression browser
- An application returning >5% HTTP 500 errors for 5 minutes triggers the `HighErrorRate` alert
- A pod restarting >5 times in an hour triggers `PodCrashLooping`
- The Alertmanager groups alerts by namespace and routes critical alerts to the pagerduty receiver
- The inhibition rule suppresses `HighLatencyP99` when `HighErrorRate` is already firing for the same service

## Acceptance Criteria

- `prometheus.yml` defines four scrape jobs with Kubernetes service discovery and correct relabeling
- Recording rules compute request rate, error rate, P99/P50 latency, CPU utilization, and memory utilization
- Six alerting rules fire at the specified thresholds and durations with correct labels and annotations
- The Alertmanager configuration routes alerts by severity, groups by namespace, and includes an inhibition rule
- All YAML files are syntactically valid and parseable by `promtool check config` and `promtool check rules`
