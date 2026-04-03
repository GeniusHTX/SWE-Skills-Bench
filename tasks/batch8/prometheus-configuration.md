# Task: Build a Prometheus Configuration Generator and Validator

## Background

Prometheus (https://github.com/prometheus/prometheus) is an open-source monitoring and alerting toolkit. The project needs a Python module that programmatically generates Prometheus configurations: scrape configs with service discovery, recording rules for pre-computing expensive queries, alerting rules with multi-window burn rate conditions, and relabeling rules for metric transformation. The generator must produce valid Prometheus YAML and validate configurations against common errors.

## Files to Create/Modify

- `documentation/examples/config_generator.py` (create) — `PrometheusConfigGenerator` class producing complete prometheus.yml configurations with global settings, scrape configs, and remote write/read endpoints
- `documentation/examples/rule_generator.py` (create) — `RuleGenerator` class creating recording rules for SLI computation and alerting rules with multi-window burn rate detection for SLO-based alerting
- `documentation/examples/relabel_engine.py` (create) — `RelabelEngine` class generating relabel_configs and metric_relabel_configs for common patterns: label extraction, metric filtering, target filtering, and label mapping
- `documentation/examples/config_validator.py` (create) — `ConfigValidator` class checking Prometheus configuration YAML for errors: invalid duration formats, duplicate job names, missing required fields, malformed PromQL in rules, and unreachable targets
- `tests/test_prometheus_configuration.py` (create) — Tests for config generation, rule creation, relabeling logic, and validation

## Requirements

### PrometheusConfigGenerator

- Constructor: `PrometheusConfigGenerator(global_scrape_interval: str = "15s", global_evaluation_interval: str = "15s")`
- `add_scrape_config(job_name: str, targets: list[str] = None, metrics_path: str = "/metrics", scheme: str = "http", scrape_interval: str = None, params: dict = None) -> None`:
  - Static targets: `static_configs: [{targets: [...]}]`
  - If `scrape_interval` is None, inherit from global
  - Validate `scheme` is `"http"` or `"https"`
- `add_kubernetes_sd(job_name: str, role: str, namespaces: list[str] = None, relabel_configs: list[dict] = None) -> None`:
  - `kubernetes_sd_configs` with `role` (one of `"node"`, `"pod"`, `"service"`, `"endpoints"`, `"ingress"`)
  - Optional namespace filtering
  - Include standard relabel configs for the role (e.g., pod role: extract pod name, namespace, container name as labels)
- `add_remote_write(url: str, queue_config: dict = None, write_relabel_configs: list[dict] = None) -> None`
- `add_rule_files(paths: list[str]) -> None`
- `generate() -> dict` — Return the complete configuration dict
- `to_yaml() -> str` — Serialize to YAML string
- Duplicate `job_name`: raise `ValueError("Duplicate job name: {name}")`

### RuleGenerator

- `recording_rule(record: str, expr: str, labels: dict = None) -> dict` — Single recording rule: `{"record": str, "expr": str, "labels": dict}`
- `alerting_rule(alert: str, expr: str, for_duration: str, labels: dict, annotations: dict) -> dict` — Single alerting rule with `for`, `labels` (must include `severity`), `annotations` (must include `summary` and `description`)
- `sli_recording_rules(service: str, error_metric: str, total_metric: str) -> list[dict]`:
  - Generate 4 multi-window recording rules for burn rate:
    - `sli:{service}:error_rate_5m` = `rate({error_metric}[5m]) / rate({total_metric}[5m])`
    - `sli:{service}:error_rate_30m` = same with 30m window
    - `sli:{service}:error_rate_1h` = same with 1h window
    - `sli:{service}:error_rate_6h` = same with 6h window
- `burn_rate_alerts(service: str, slo_target: float, page_severity: str = "critical", ticket_severity: str = "warning") -> list[dict]`:
  - **Page alert** (fast burn): 5m rate > `14.4 × (1 - slo_target)` AND 1h rate > `14.4 × (1 - slo_target)`, `for: "2m"`, severity = page_severity
  - **Ticket alert** (slow burn): 30m rate > `6 × (1 - slo_target)` AND 6h rate > `6 × (1 - slo_target)`, `for: "5m"`, severity = ticket_severity
  - Annotations include current error rate and SLO target in description
- `rule_group(name: str, interval: str, rules: list[dict]) -> dict` — Wrap rules in a group: `{"name": str, "interval": str, "rules": list}`
- `to_yaml(groups: list[dict]) -> str` — Serialize rule file: `{"groups": [...]}`

### RelabelEngine

- `keep_by_label(source_label: str, regex: str) -> dict` — `relabel_config` that keeps targets matching regex on source label
- `drop_by_label(source_label: str, regex: str) -> dict` — Drop targets matching regex
- `rename_label(source: str, target: str) -> dict` — Copy label value from source to target using `replacement: "$1"`
- `extract_from_label(source: str, regex: str, target: str) -> dict` — Extract a capture group from source label and write to target
- `drop_metric(metric_name_regex: str) -> dict` — `metric_relabel_config` dropping metrics matching name pattern
- `aggregate_labels(source_labels: list[str], separator: str, target: str) -> dict` — Concatenate multiple source labels with separator into target label
- `kubernetes_pod_relabels() -> list[dict]` — Standard set for pod SD: extract `__meta_kubernetes_pod_name` → `pod`, `__meta_kubernetes_namespace` → `namespace`, `__meta_kubernetes_pod_container_name` → `container`, keep only pods with annotation `prometheus.io/scrape: "true"`, extract port from `prometheus.io/port` annotation

### ConfigValidator

- `validate_config(config: dict) -> list[str]` — Return errors:
  - Invalid duration format (must match `[0-9]+(ms|s|m|h|d|w|y)`): `"Invalid duration '{value}' in {location}"`
  - Duplicate job names: `"Duplicate job name: '{name}'"`
  - Missing `targets` in static config and no service discovery: `"Job '{name}' has no targets and no service discovery"`
  - Invalid scheme: `"Invalid scheme '{scheme}' in job '{name}'"`
- `validate_rules(rule_file: dict) -> list[str]` — Return errors:
  - Missing `expr` in rule: `"Rule '{name}' missing 'expr'"`
  - Alert without `for` duration: `"Alert '{name}' missing 'for' duration"`
  - Alert without `severity` label: `"Alert '{name}' missing severity label"`
  - Duplicate rule names within a group: `"Duplicate rule name '{name}' in group '{group}'"`
- `validate_relabel(relabel_config: dict) -> list[str]`:
  - Missing `source_labels` when `action` requires it: `"Action '{action}' requires source_labels"`
  - Invalid regex: `"Invalid regex '{regex}' in relabel config"`

### Edge Cases

- Duration `"0s"`: valid but log a warning
- Empty targets list: valid for service-discovery-based jobs, error for static-only jobs
- Recording rule with no labels: valid (labels field is optional)
- Alert with `for: "0s"`: valid (fires immediately)
- SLO target of 1.0 (100%): burn rate threshold becomes 0, generating `expr` that triggers on any error

## Expected Functionality

- `PrometheusConfigGenerator` with 3 scrape configs (node exporter, kube-state-metrics, application) produces valid prometheus.yml
- `RuleGenerator.sli_recording_rules("api", "http_errors_total", "http_requests_total")` produces 4 multi-window rate recording rules
- `RuleGenerator.burn_rate_alerts("api", 0.999)` produces page and ticket alerts with thresholds: `0.0144` and `0.006`
- `RelabelEngine.kubernetes_pod_relabels()` produces relabel configs that filter and label Kubernetes pod targets
- `ConfigValidator` catches a scrape config with `scheme: "ftp"` and a rule missing the `expr` field

## Acceptance Criteria

- Generated prometheus.yml is valid YAML with correct structure for scrape configs, SD configs, and remote write
- Recording rules compute SLI error rates at multiple windows (5m, 30m, 1h, 6h)
- Alerting rules implement multi-window burn rate detection with correct thresholds based on SLO target
- Relabel configs use correct Prometheus relabeling actions and regex syntax
- Validator catches invalid durations, duplicate jobs, missing fields, and malformed rules
- All tests pass with `pytest`
