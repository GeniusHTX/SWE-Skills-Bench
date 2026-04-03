# Task: Implement SLI/SLO Recording Rules and Error Budget Alerts for slo-generator

## Background

The `google/slo-generator` repository provides a framework for computing SLIs and SLOs from time-series backends. The project currently lacks a complete end-to-end example that wires together a Prometheus backend SLI definition, multi-window multi-burn-rate alerting rules, and an error budget policy with automated freeze logic.

## Files to Create/Modify

- `samples/prometheus/slo_prometheus_api_availability.yaml` (create) — SLO definition YAML targeting 99.9% availability SLO over a 28-day window using `http_requests_total` metrics
- `samples/prometheus/slo_prometheus_api_latency.yaml` (create) — SLO definition YAML targeting 99% of requests under 500ms latency threshold
- `samples/prometheus/prometheus_rules.yaml` (create) — Prometheus recording rules and multi-window burn rate alert rules derived from the two SLO definitions above
- `slo_generator/backends/prometheus.py` (modify) — Add `compute_error_budget_remaining(slo_config, current_sli_value)` method that returns remaining error budget as a float between 0 and 1
- `tests/unit/test_prometheus_backend.py` (modify) — Add tests for `compute_error_budget_remaining` covering normal, depleted, and over-budget cases

## Requirements

### SLO Definition Files

- `slo_prometheus_api_availability.yaml` must specify `backend: prometheus`, a `measurement` section using `http_requests_total` with a filter for non-5xx responses as the good event count and all requests as the total, `goal: 0.999`, and `window: 28d`
- `slo_prometheus_api_latency.yaml` must specify `backend: prometheus`, a latency-based `measurement` using `http_request_duration_seconds_bucket` with `le="0.5"` as the threshold for good requests, `goal: 0.99`, and `window: 28d`
- Both files must include `service_name`, `feature_name`, and `slo_name` fields following the existing sample naming conventions in the repository

### Prometheus Recording Rules

- `prometheus_rules.yaml` must define a `record` rule group that produces `slo:sli_value:ratio_rate28d` for each SLO using the same PromQL logic as the SLO definitions
- Multi-window burn rate alert rules must be defined for 1h/6h fast burn (`burn_rate > 14.4`) and 6h/3d slow burn (`burn_rate > 6`) windows for each SLO
- Alert rules must carry labels `slo_name`, `service`, `severity` and annotations `summary` and `description` with concrete metric values interpolated
- Alert names must follow the pattern `SLO<ServiceName><SloType>BurnRateLow` and `SLO<ServiceName><SloType>BurnRateHigh`

### Backend Method

- `compute_error_budget_remaining(slo_config, current_sli_value)` must extract `goal` from `slo_config`, compute `error_budget = 1 - goal`, compute `consumed = (goal - current_sli_value) / error_budget` (clamped at 0), and return `remaining = 1 - consumed`
- Return value must be clamped to `[0.0, 1.0]`; if `current_sli_value >= goal`, return 1.0; if error budget is fully consumed or exceeded, return 0.0
- Raise `ValueError` if `goal` is not in `(0, 1)` exclusive range

### Expected Functionality

- `compute_error_budget_remaining({"goal": 0.999}, 0.9985)` → approximately 0.5 (50% remaining)
- `compute_error_budget_remaining({"goal": 0.999}, 0.999)` → 1.0
- `compute_error_budget_remaining({"goal": 0.999}, 0.998)` → 0.0 (budget exhausted)
- `compute_error_budget_remaining({"goal": 0.999}, 0.9975)` → 0.0 (over budget)
- `compute_error_budget_remaining({"goal": 1.5}, ...)` → raises `ValueError`
- `compute_error_budget_remaining({"goal": 0.0}, ...)` → raises `ValueError`

## Acceptance Criteria

- `samples/prometheus/slo_prometheus_api_availability.yaml` and `slo_prometheus_api_latency.yaml` are valid YAML parseable by `slo_generator` without schema errors and use the correct `backend: prometheus` fields
- `samples/prometheus/prometheus_rules.yaml` contains recording rules for both SLOs and at least four alert rules (fast/slow burn for each) with correct burn-rate thresholds
- `compute_error_budget_remaining` returns values in `[0.0, 1.0]`, returns 1.0 when SLI meets or exceeds the goal, returns 0.0 when SLI breaches the error budget entirely, and raises `ValueError` for out-of-range goal values
- Unit tests cover all specified scenarios including normal operation, depletion, over-budget, and invalid input
- `python -m pytest tests/unit/test_prometheus_backend.py -v` passes after changes
