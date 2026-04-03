# Task: Add Multi-Tier Scrape Configuration and Recording Rules for Prometheus

## Background

The Prometheus monitoring system needs a new scrape configuration tier and a set of recording rules to support monitoring a microservices deployment. The existing `config/` package handles YAML configuration parsing and validation, but it lacks coverage for a realistic multi-job scrape setup with relabeling, file-based service discovery, and pre-aggregated recording rules. The configuration must be added so that Prometheus can scrape application metrics from multiple service tiers, apply relabeling to normalize labels, and evaluate recording rules that pre-compute request rates, error percentages, and latency quantiles.

## Files to Create/Modify

- `config/testdata/multi_tier_scrape.yml` (create) — Full Prometheus configuration file with global settings, multiple scrape jobs, relabel configs, and file-based service discovery
- `config/testdata/recording_rules.yml` (create) — Recording rules file defining pre-aggregated metrics for HTTP request rates, error rates, and latency percentiles
- `config/testdata/alert_rules.yml` (create) — Alert rules file with availability and latency alerts referencing the recording rule outputs
- `config/testdata/file_sd_targets.json` (create) — File-based service discovery target list in JSON format
- `config/config_test.go` (modify) — Add test cases that load and validate the new configuration files
- `rules/recording_test.go` (modify) — Add test cases that parse and evaluate the new recording rules

## Requirements

### Global Configuration

- `scrape_interval` set to `15s`, `evaluation_interval` set to `15s`
- `external_labels` must include `cluster: "production"` and `region: "us-west-2"`
- Alertmanager target configured as a static target at `alertmanager:9093`
- `rule_files` glob pointing to the recording and alert rule YAML files

### Scrape Configurations

- A `prometheus` job scraping `localhost:9090` with static config
- A `node-exporter` job scraping three static targets (`node1:9100`, `node2:9100`, `node3:9100`) with a relabel config that extracts the hostname from `__address__` and writes it to the `instance` label, stripping the port
- An `application-api` job using `file_sd_configs` reading from `file_sd_targets.json` with a `refresh_interval` of `5m`; this job must set `metrics_path` to `/internal/metrics` and apply a relabel config that adds a `service_tier` label derived from the `__meta_filepath` source label
- A `kubernetes-pods` job using `kubernetes_sd_configs` with `role: pod`; relabel configs must keep only pods annotated with `prometheus.io/scrape: "true"`, replace `__metrics_path__` from the `prometheus.io/path` annotation, construct `__address__` from the pod IP and `prometheus.io/port` annotation, and copy `__meta_kubernetes_namespace` and `__meta_kubernetes_pod_name` into `namespace` and `pod` labels respectively

### File-Based Service Discovery

- `file_sd_targets.json` must contain two target groups:
  - Group 1: targets `["api-1:9090", "api-2:9090"]` with labels `env: "production"`, `service: "api-gateway"`
  - Group 2: targets `["worker-1:9090", "worker-2:9090", "worker-3:9090"]` with labels `env: "production"`, `service: "background-worker"`

### Recording Rules

- Rule group `http_metrics` with `interval: 15s` containing:
  - `job:http_requests:rate5m` — sum by `job` of `rate(http_requests_total[5m])`
  - `job:http_requests_errors:rate5m` — sum by `job` of `rate(http_requests_total{status=~"5.."}[5m])`
  - `job:http_requests_error_rate:percentage` — ratio of the above two rules multiplied by 100
  - `job:http_request_duration:p95` — `histogram_quantile(0.95, sum by (job, le) (rate(http_request_duration_seconds_bucket[5m])))`
- Rule group `resource_metrics` with `interval: 30s` containing:
  - `instance:node_cpu:utilization` — 100 minus the average idle CPU rate per instance over 5 minutes
  - `instance:node_memory:utilization` — percentage of memory used, computed from `node_memory_MemAvailable_bytes` and `node_memory_MemTotal_bytes`
  - `instance:node_disk:utilization` — percentage of disk used, computed from `node_filesystem_avail_bytes` and `node_filesystem_size_bytes`

### Alert Rules

- Rule group `availability` with `interval: 30s`:
  - `ServiceDown` — fires when `up{job="application-api"} == 0` for 1 minute; severity `critical`; annotations must include `summary` and `description` templates using `{{ $labels.instance }}` and `{{ $labels.job }}`
  - `HighErrorRate` — fires when `job:http_requests_error_rate:percentage > 5` for 5 minutes; severity `warning`; annotation `description` must include `{{ $value }}`
  - `HighP95Latency` — fires when `job:http_request_duration:p95 > 0.5` for 10 minutes; severity `warning`

### Expected Functionality

- Loading `multi_tier_scrape.yml` with `config.Load()` succeeds and returns a `Config` struct with exactly 4 scrape configs
- The `node-exporter` scrape config contains a `RelabelConfig` with `regex` that matches `([^:]+)(:[0-9]+)?` and `replacement` set to `${1}`
- The `application-api` scrape config has `MetricsPath` equal to `/internal/metrics` and contains a `FileSDConfig` entry
- The `kubernetes-pods` scrape config has 5 relabel configs (keep, replace path, replace address, replace namespace, replace pod)
- Parsing `recording_rules.yml` with `rules.Parse()` produces 2 rule groups with 4 and 3 rules respectively
- Parsing `alert_rules.yml` produces 1 rule group with 3 alerting rules
- The `ServiceDown` alert has `For` duration of 1 minute and label `severity: "critical"`
- `file_sd_targets.json` parses as valid JSON containing 2 target groups with 2 and 3 targets respectively
- A malformed YAML file (missing required `job_name` in a scrape config) is rejected by `config.Load()` with an error

## Acceptance Criteria

- All new YAML/JSON files parse without errors using Prometheus's own config and rules packages
- `go test ./config/ -run TestMultiTierScrape -v` passes, validating that the configuration loads and all scrape jobs, relabel rules, and service discovery entries are present with correct values
- `go test ./rules/ -run TestRecordingRules -v` passes, validating that recording rules parse into the correct number of groups and rules with expected metric names and expressions
- Alert rules contain correct `for` durations, label sets, and annotation templates
- The relabel config for `node-exporter` correctly strips ports from `__address__` and writes to `instance`
- The Kubernetes pod relabel chain has exactly 5 entries with the correct source labels, actions, and target labels
- No hardcoded metric values appear in test assertions — all checks validate structure and configuration correctness
