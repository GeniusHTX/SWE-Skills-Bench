# Task: Add Custom Service Discovery and Alert Rule Configuration for Prometheus

## Background

Prometheus (https://github.com/prometheus/prometheus) is an open-source monitoring and alerting system. The project needs a new configuration module that generates Prometheus scrape configurations with custom service discovery, recording rules for aggregated metrics, and multi-severity alert rules. The configurations must follow Prometheus's YAML schema and integrate with its existing configuration loading in the `config/` package.

## Files to Create/Modify

- `config/service_discovery.go` (create) — Custom file-based service discovery configuration generator
- `rules/recording_rules.go` (create) — Recording rule generator for commonly aggregated metrics
- `rules/alert_rules.go` (create) — Alert rule generator with multi-severity support and burn rate conditions
- `config/service_discovery_test.go` (create) — Tests for service discovery configuration
- `rules/recording_rules_test.go` (create) — Tests for recording rule generation
- `rules/alert_rules_test.go` (create) — Tests for alert rule generation

## Requirements

### Service Discovery Configuration

- Implement a `ServiceDiscoveryConfig` struct and `GenerateFileSD` function that produces JSON target files for Prometheus's file-based service discovery
- Each target entry contains: `targets` (list of `host:port` strings), `labels` (map of key-value label pairs including `job`, `environment`, `region`)
- Validate target format: must match `hostname:port` pattern where port is 1–65535; return error for invalid targets
- Validate label names: must match `[a-zA-Z_][a-zA-Z0-9_]*`; `__`-prefixed labels are reserved and must be rejected
- Support generating targets for multiple environments (e.g., `production`, `staging`) in a single call, producing separate target groups per environment

### Recording Rules

- Implement a `RecordingRuleGenerator` that creates recording rules for the four golden signals:
  - **Latency**: `job:http_request_duration_seconds:p50`, `:p90`, `:p99` — quantile aggregations from histogram
  - **Traffic**: `job:http_requests_total:rate5m` — rate of incoming requests per job
  - **Errors**: `job:http_errors:ratio_rate5m` — error rate as a ratio of total requests
  - **Saturation**: `job:process_cpu_seconds_total:rate5m` — CPU utilization per job
- Each rule specifies: `record` (metric name), `expr` (PromQL expression), optional `labels`
- Group rules by signal type: all latency rules in one group, traffic in another, etc.
- Rule names must follow the naming convention: `level:metric:operations` (e.g., `job:http_request_duration_seconds:percentile_99`)

### Alert Rules

- Implement an `AlertRuleGenerator` that creates multi-severity alert rules:
  - `critical` alerts: page immediately, used for user-impacting issues (e.g., error rate > 5% for 5 minutes)
  - `warning` alerts: trigger ticket creation, used for degraded performance (e.g., p99 latency > 1s for 15 minutes)
  - `info` alerts: log only, used for early indicators (e.g., p90 latency > 500ms for 30 minutes)
- Each alert rule has: `alert` (name), `expr` (PromQL), `for` (duration), `labels` (including `severity`), `annotations` (including `summary` and `description` with templated values using `{{ $value }}`)
- Support burn-rate alerts for SLO violations: e.g., burn rate > 14.4 in 5-minute window AND > 14.4 in 1-hour window triggers critical
- Generate an inhibition rule: critical alerts suppress warning alerts for the same `job` and `alertname`

### YAML Output

- All generated configurations must produce valid Prometheus YAML
- Provide a `MarshalYAML() ([]byte, error)` method on each configuration type
- The YAML output must round-trip: unmarshaling the output back into the struct produces an equivalent configuration

### Expected Functionality

- Generating file SD for 3 hosts in production and 2 in staging produces 2 target groups with correct labels
- A target `"invalid:99999"` fails validation (port out of range)
- A label name `"__internal"` fails validation (reserved prefix)
- Recording rules for latency produce 3 rules (p50, p90, p99) with correct PromQL histogram_quantile expressions
- Alert rules for critical error rate produce a rule with `expr: job:http_errors:ratio_rate5m > 0.05` and `for: 5m`
- The YAML output for recording rules is valid and parseable by Prometheus's rule file loader

## Acceptance Criteria

- Service discovery generates valid JSON target files with correct `targets` and `labels` structure
- Target and label validation rejects invalid formats with descriptive error messages
- Recording rules cover all four golden signals with correct PromQL expressions
- Rule names follow the `level:metric:operations` convention
- Alert rules support three severity levels with correct `for` durations and annotation templates
- Burn-rate alert rules use multi-window conditions
- Inhibition rules suppress lower-severity alerts when higher-severity ones are firing
- YAML output is valid and round-trips correctly
- Tests cover valid configurations, validation errors, all signal types, and YAML serialization
