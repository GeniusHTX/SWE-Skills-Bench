# Task: Create a Complete Prometheus Monitoring Configuration for a Microservices Stack

## Background

Prometheus (https://github.com/prometheus/prometheus) is being configured to monitor a microservices application consisting of four services: `api-gateway` (port 8080), `user-service` (port 8081), `order-service` (port 8082), and `payment-service` (port 8083). Each service exposes a `/metrics` endpoint. The configuration must include scrape configs, recording rules for pre-computed aggregations, and alerting rules for SLO-based monitoring.

## Files to Create/Modify

- `documentation/examples/microservices/prometheus.yml` (create) — Main Prometheus configuration with global settings, alertmanager config, rule file references, and scrape configurations for all four services plus Prometheus self-monitoring
- `documentation/examples/microservices/rules/recording_rules.yml` (create) — Recording rules for pre-aggregated metrics: request rate, error rate, and latency percentiles per service
- `documentation/examples/microservices/rules/alerting_rules.yml` (create) — Alerting rules for SLO violations: high error rate, high latency, service down, and saturation alerts
- `documentation/examples/microservices/rules/slo_rules.yml` (create) — SLO burn rate recording rules and multi-window alerts based on the Google SRE error budget methodology
- `documentation/examples/microservices/docker-compose.yml` (create) — Docker Compose file running Prometheus with the configuration and an Alertmanager instance

## Requirements

### Main Configuration (`prometheus.yml`)

- `global.scrape_interval`: 15s
- `global.evaluation_interval`: 15s
- `global.external_labels`: `cluster: "production"`, `environment: "prod"`
- `alerting.alertmanagers`: static config targeting `alertmanager:9093`
- `rule_files`: include all three rules files from `rules/` directory using glob `rules/*.yml`
- Scrape configs:
  - `prometheus` job: scrape `localhost:9090` (self-monitoring)
  - `api-gateway` job: scrape `api-gateway:8080` with `metrics_path: /metrics`, add `relabel_configs` to set `service` label to `api-gateway`
  - `user-service` job: scrape `user-service:8081`
  - `order-service` job: scrape `order-service:8082`
  - `payment-service` job: scrape `payment-service:8083` with `scrape_interval: 10s` (overriding global for critical payment path)
- Each service scrape config must include `metric_relabel_configs` that drop metrics matching the regex `go_gc_.*` to reduce storage cardinality

### Recording Rules (`recording_rules.yml`)

- Rule group name: `service_metrics`
- Evaluation interval: 15s
- Rules:
  - `service:http_requests:rate5m` — `sum(rate(http_requests_total[5m])) by (service, method, status_code)`
  - `service:http_errors:rate5m` — `sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (service)`
  - `service:http_request_duration_seconds:p50` — `histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (service, le))`
  - `service:http_request_duration_seconds:p95` — Same with 0.95
  - `service:http_request_duration_seconds:p99` — Same with 0.99
  - `service:http_error_ratio:rate5m` — `service:http_errors:rate5m / clamp_min(sum(rate(http_requests_total[5m])) by (service), 1)` (using `clamp_min` to avoid division by zero)

### Alerting Rules (`alerting_rules.yml`)

- Rule group name: `service_alerts`
- Alerts:
  - `HighErrorRate` — Fires when `service:http_error_ratio:rate5m > 0.05` for 5 minutes; severity: `critical`; include `service` label in annotations with a human-readable summary
  - `HighP95Latency` — Fires when `service:http_request_duration_seconds:p95 > 0.5` for 5 minutes; severity: `warning`
  - `ServiceDown` — Fires when `up == 0` for 1 minute; severity: `critical`; include `instance` and `job` in annotations
  - `HighMemoryUsage` — Fires when `process_resident_memory_bytes / (1024^3) > 1.5` for 10 minutes; severity: `warning`

### SLO Rules (`slo_rules.yml`)

- Rule group name: `slo_burn_rate`
- Target SLO: 99.9% availability (error budget: 0.1%)
- Recording rules for error burn rates over multiple windows:
  - `slo:error_budget:burn_rate_1h` — `1 - (sum(rate(http_requests_total{status_code!~"5.."}[1h])) / sum(rate(http_requests_total[1h])))`
  - `slo:error_budget:burn_rate_6h` — Same with 6h window
  - `slo:error_budget:burn_rate_24h` — Same with 24h window
- Multi-window alert `SLOBudgetBurnHigh` — Fires when both `slo:error_budget:burn_rate_1h > 14.4 * 0.001` AND `slo:error_budget:burn_rate_6h > 6 * 0.001` for 5 minutes; severity: `critical`

### Docker Compose (`docker-compose.yml`)

- Service `prometheus` using `prom/prometheus:latest`, mounting `prometheus.yml` and `rules/` directory, port `9090:9090`, command flags include `--config.file`, `--storage.tsdb.retention.time=30d`, `--web.enable-lifecycle`
- Service `alertmanager` using `prom/alertmanager:latest`, port `9093:9093`

### Expected Functionality

- `promtool check config prometheus.yml` validates the config without errors
- `promtool check rules rules/recording_rules.yml` validates recording rules
- `promtool check rules rules/alerting_rules.yml` validates alerting rules
- `promtool check rules rules/slo_rules.yml` validates SLO rules
- All recording rules produce valid PromQL expressions
- The `payment-service` scrape interval is 10s while other services use the global 15s default

## Acceptance Criteria

- `promtool check config documentation/examples/microservices/prometheus.yml` exits with code 0
- `promtool check rules` passes for all three rule files without errors
- The main config scrapes 5 targets (4 services + self) with correct ports
- Recording rules produce 6 pre-aggregated metric names
- Alerting rules define 4 alerts with correct `for` durations and severity labels
- SLO burn rate rules implement multi-window alerting with correct budget thresholds
- `go_gc_.*` metrics are dropped via `metric_relabel_configs` on all service scrape configs
- `python -m pytest /workspace/tests/test_prometheus_configuration.py -v --tb=short` passes
