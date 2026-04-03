# Task: Add Custom Prometheus Scrape and Recording Rules for a Multi-Service Application

## Background

The Prometheus repository (https://github.com/prometheus/prometheus) provides a monitoring system and time-series database. A production deployment needs a complete Prometheus configuration for monitoring a multi-service application stack consisting of an API gateway, three backend microservices, a PostgreSQL database, and a Redis cache. The configuration must include scrape targets, relabeling rules, recording rules for pre-computed aggregations, and alert rules for availability and resource thresholds.

## Files to Create/Modify

- `documentation/examples/custom-app/prometheus.yml` (create) — Main Prometheus configuration with global settings, scrape configs, and rule file references
- `documentation/examples/custom-app/rules/recording_rules.yml` (create) — Recording rules for pre-computed query aggregations
- `documentation/examples/custom-app/rules/alert_rules.yml` (create) — Alert rules for availability, latency, and resource usage
- `documentation/examples/custom-app/targets/services.json` (create) — File-based service discovery target definitions

## Requirements

### Main Configuration (`prometheus.yml`)

- Global scrape interval set to 15 seconds; evaluation interval set to 15 seconds
- External labels: `cluster: "production"`, `environment: "prod"`
- AlertManager target configured at `alertmanager:9093`
- Rule files loaded from `rules/*.yml`
- Scrape configs for the following jobs:
  - `prometheus` — self-monitoring at `localhost:9090`
  - `api-gateway` — static target at `gateway:8080` with metrics path `/metrics` and HTTPS scheme using TLS config referencing `/etc/prometheus/ca.crt`
  - `backend-services` — file-based service discovery reading from `targets/services.json`, with refresh interval of 5 minutes
  - `postgres-exporter` — static target at `postgres-exporter:9187` with relabel config adding label `db_instance: "primary"`
  - `redis-exporter` — static target at `redis-exporter:9121`
  - `kubernetes-pods` — Kubernetes pod SD with relabel configs that keep only pods with annotation `prometheus.io/scrape: "true"` and extract metrics path and port from annotations

### Service Discovery File (`targets/services.json`)

- Define three backend services: `user-service:9090`, `order-service:9090`, `payment-service:9090`
- Each target group must include labels for `env: "production"` and a `service` label identifying the specific service name

### Recording Rules

- `job:http_requests_total:rate5m` — 5-minute rate of HTTP requests per job
- `job:http_request_duration_seconds:p99` — 99th percentile request latency per job over a 5-minute window
- `job:http_request_errors:rate5m` — 5-minute rate of 5xx HTTP responses per job
- `instance:node_cpu_utilization:ratio` — CPU utilization ratio per instance (1 minus idle rate)
- `instance:node_memory_utilization:ratio` — Memory utilization ratio per instance
- All recording rules must be in a group named `custom_app_recording_rules` with an interval of 30 seconds

### Alert Rules

- `HighErrorRate` — fires when the 5xx error rate for any job exceeds 5% of total requests for 5 minutes; severity label `critical`
- `HighLatency` — fires when p99 latency exceeds 500ms for 10 minutes; severity label `warning`
- `ServiceDown` — fires when `up == 0` for any target for 2 minutes; severity label `critical`
- `HighCPU` — fires when CPU utilization exceeds 80% for 15 minutes; severity label `warning`
- `HighMemory` — fires when memory utilization exceeds 85% for 10 minutes; severity label `warning`
- `DiskSpaceRunningLow` — fires when filesystem available space drops below 15% for 10 minutes; severity label `critical`
- All alerts must include an `annotations` block with `summary` and `description` fields that include template variables (e.g., `{{ $labels.instance }}`)
- Alert rules must be in a group named `custom_app_alerts`

### Configuration Validity

- `prometheus.yml` must pass `promtool check config` without errors
- Recording rule and alert rule files must pass `promtool check rules` without errors
- YAML syntax must be valid; no tabs, proper indentation

### Expected Functionality

- Prometheus starts with the configuration and successfully scrapes all static targets
- File-based service discovery loads the three backend services and scrapes them on the standard interval
- Recording rules produce pre-computed metrics queryable as `job:http_requests_total:rate5m`, etc.
- The `ServiceDown` alert transitions to `FIRING` when any target becomes unreachable for 2+ minutes
- The `HighErrorRate` alert transitions to `FIRING` when more than 5% of requests return 5xx for 5+ minutes
- Kubernetes pod SD relabeling correctly filters to annotated pods and extracts custom metrics paths

## Acceptance Criteria

- All configuration files are valid YAML that pass `promtool` validation
- `prometheus.yml` defines scrape configs for all six required jobs with correct targets, schemes, and relabeling
- File-based service discovery file contains the three backend services with proper label sets
- Recording rules produce the five specified pre-computed metrics
- Alert rules define the six specified alerts with correct thresholds, durations, severity labels, and annotation templates
- Kubernetes pod SD relabel config correctly keeps only annotated pods and extracts annotation-based metrics path and port
