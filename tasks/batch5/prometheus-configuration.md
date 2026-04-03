# Task: Configure Prometheus Monitoring for a Microservices Stack

## Background

Prometheus (https://github.com/prometheus/prometheus) is the industry-standard monitoring and alerting toolkit. This task requires creating a complete Prometheus configuration for monitoring a hypothetical microservices deployment: an API gateway, a user service, and an order service. The configuration must include scrape targets, recording rules for aggregated metrics, and alerting rules for SLO-based burndown alerts.

## Files to Create/Modify

- `documentation/examples/microservices/prometheus.yml` (create) — Main Prometheus configuration with global settings, scrape configs for 3 services, and rule file references.
- `documentation/examples/microservices/rules/recording_rules.yml` (create) — Recording rules computing: request rate per service (5m window), error rate per service, P99 latency per service, and availability ratio.
- `documentation/examples/microservices/rules/alerting_rules.yml` (create) — Alerting rules: high error rate (>1% over 5m), high latency (P99 > 500ms over 10m), service down (absent metric for 2m), and error budget burn rate alerts (multi-window).
- `documentation/examples/microservices/targets/api_gateway.json` (create) — File-based service discovery target list for the API gateway (3 instances).
- `documentation/examples/microservices/targets/services.json` (create) — File-based service discovery for user-service (2 instances) and order-service (2 instances).
- `documentation/examples/microservices/tests/test_prometheus_config.py` (create) — Test script that validates YAML syntax, checks required labels, verifies alert expression syntax, and ensures recording rules produce valid PromQL.

## Requirements

### Global Configuration

- `scrape_interval: 15s`, `evaluation_interval: 15s`.
- `external_labels`: `cluster: production`, `environment: prod`.

### Scrape Configs

- **api-gateway**: `file_sd_configs` reading from `targets/api_gateway.json`, metrics path `/metrics`, scrape interval `10s`, relabel to add `service=api-gateway` label.
- **user-service**: `file_sd_configs` reading from `targets/services.json`, use `__meta_filepath` relabeling to select only user-service targets, metrics path `/actuator/prometheus`, scheme `http`.
- **order-service**: same file_sd_configs, filtered for order-service targets, metrics path `/metrics`.
- All scrape configs include `honor_labels: false` and a `metric_relabel_configs` rule dropping metrics with the prefix `go_` (reduce cardinality).

### Recording Rules (Group: `microservices_sli`)

- `service:http_requests:rate5m` = `sum(rate(http_requests_total[5m])) by (service)`.
- `service:http_errors:rate5m` = `sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)`.
- `service:http_error_ratio:rate5m` = `service:http_errors:rate5m / service:http_requests:rate5m`.
- `service:http_latency_p99:rate5m` = `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (service, le))`.
- `service:availability:rate5m` = `1 - service:http_error_ratio:rate5m`.

### Alerting Rules (Group: `microservices_alerts`)

- **HighErrorRate**: `service:http_error_ratio:rate5m > 0.01` for 5m → severity: warning.
- **CriticalErrorRate**: `service:http_error_ratio:rate5m > 0.05` for 2m → severity: critical.
- **HighLatency**: `service:http_latency_p99:rate5m > 0.5` for 10m → severity: warning (0.5 = 500ms).
- **ServiceDown**: `absent(up{service="api-gateway"} == 1)` for 2m → severity: critical (one rule per service).
- **ErrorBudgetFastBurn**: `service:http_error_ratio:rate5m > (14.4 * 0.001)` and `service:http_error_ratio:rate1h > (14.4 * 0.001)` → severity: critical (1h/5m multi-window burn).

### Service Discovery Files

- `api_gateway.json`: `[{"targets": ["gateway-1:9090", "gateway-2:9090", "gateway-3:9090"], "labels": {"service": "api-gateway", "team": "platform"}}]`.
- `services.json`: two entries — one for user-service (targets: `user-1:8080`, `user-2:8080`) and one for order-service (targets: `order-1:8080`, `order-2:8080`).

### Expected Functionality

- `promtool check config prometheus.yml` → valid configuration.
- `promtool check rules rules/recording_rules.yml` → valid rules.
- `promtool check rules rules/alerting_rules.yml` → valid rules.
- When `service:http_error_ratio:rate5m` for `api-gateway` exceeds 0.01 for 5 minutes → `HighErrorRate` alert fires with `service=api-gateway` label.

## Acceptance Criteria

- `prometheus.yml` is valid YAML and passes `promtool check config`.
- All three services are scraped with correct paths, intervals, and relabeling.
- The `go_` metrics are dropped via metric relabeling.
- Recording rules compute 5 SLI metrics with correct PromQL.
- Alerting rules define 5 alerts with correct thresholds, durations, and severity labels.
- Service discovery JSON files define all 7 target instances across 3 services.
- Tests validate YAML syntax, PromQL expression structure, and completeness of configuration.
