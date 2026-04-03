# Task: Implement SLO Definitions and Error Budget Tracking for slo-generator

## Background

The slo-generator project (https://github.com/google/slo-generator) is a Python tool for computing SLI/SLO/error budget metrics from monitoring backends (Prometheus, Cloud Monitoring, etc.) and exporting results. The project needs a new SLO configuration for a multi-tier web application that defines availability and latency SLIs, computes error budgets over rolling windows, and produces structured reports. The configuration must cover an API service, a background worker, and a data pipeline, each with distinct SLO targets.

## Files to Create/Modify

- `samples/multi_tier/slo_config.yaml` (create) — SLO configuration defining 6 SLOs across 3 services (API, worker, pipeline) with availability and latency targets
- `samples/multi_tier/error_budget.yaml` (create) — Error budget policy defining burn-rate alerting thresholds and budget depletion actions
- `samples/multi_tier/exporters.yaml` (create) — Exporter configuration for outputting SLO reports to JSON files and BigQuery
- `slo_generator/compute.py` (modify) — Add support for a `multi_window_burn_rate` alert method that evaluates burn rate across 1h, 6h, and 3d windows simultaneously
- `slo_generator/report.py` (modify) — Add a `generate_budget_report(slo_configs, window_days)` function that produces a per-service error budget summary with remaining budget percentage, burn rate, and projected exhaustion date
- `tests/unit/test_multi_tier_slo.py` (create) — Tests validating SLO computation, error budget calculation, burn-rate alerting logic, and report generation

## Requirements

### SLO Configuration (slo_config.yaml)

- **API Service — Availability SLO**: Target 99.9% over 28-day rolling window; SLI defined as `successful_requests / total_requests` where successful means HTTP status < 500
- **API Service — Latency SLO**: Target 99% of requests complete within 500ms over 28-day rolling window; SLI defined as `requests_below_threshold / total_requests`
- **Worker Service — Availability SLO**: Target 99.5% over 28-day rolling window; SLI defined as `successful_job_completions / total_jobs_started`
- **Worker Service — Processing Time SLO**: Target 95% of jobs complete within 60 seconds over 7-day rolling window
- **Data Pipeline — Freshness SLO**: Target 99% of data records arrive within 5 minutes of generation over 28-day rolling window; SLI defined as `records_within_threshold / total_records`
- **Data Pipeline — Completeness SLO**: Target 99.9% of expected records are present over 28-day rolling window; SLI defined as `actual_records / expected_records`
- Each SLO must specify: `service_name`, `sli_type`, `target`, `window_days`, `description`, and `backend` (Prometheus query or mock)

### Error Budget Computation

- Error budget is `1 - target` as a fraction of the window (e.g., 99.9% target over 28 days = 0.1% budget = 40.32 minutes of allowed downtime)
- `remaining_budget_pct = max(0, (budget_total - budget_consumed) / budget_total * 100)`
- `burn_rate = budget_consumed_in_period / (budget_total * period_fraction)` where a burn rate of 1.0 means consuming budget exactly at the sustainable rate
- Projected exhaustion date: if current burn rate > 1.0, calculate `remaining_budget / (burn_rate - 1.0) * window_days` days until exhaustion

### Multi-Window Burn Rate Alerting

- Evaluate burn rate across three windows simultaneously: 1-hour (fast burn), 6-hour (medium burn), and 3-day (slow burn)
- **Page alert** (critical): fires when 1h burn rate > 14.4× AND 6h burn rate > 6× (rapid budget consumption)
- **Ticket alert** (warning): fires when 6h burn rate > 6× AND 3d burn rate > 3× (sustained elevated consumption)
- **Budget exhaustion alert**: fires when remaining budget < 10%
- Alert evaluation must return a structured result: `{"alert_type": str, "severity": str, "burn_rates": {"1h": float, "6h": float, "3d": float}, "remaining_budget_pct": float}`

### Budget Report Generation

- `generate_budget_report()` must accept a list of SLO configs and return a list of report entries, one per SLO
- Each report entry: `{"service": str, "slo_name": str, "target_pct": float, "current_sli_pct": float, "remaining_budget_pct": float, "burn_rate_1h": float, "burn_rate_6h": float, "burn_rate_3d": float, "projected_exhaustion_date": str | null, "status": "healthy" | "warning" | "critical"}`
- Status determination: `healthy` if remaining budget ≥ 50%, `warning` if 10% ≤ budget < 50%, `critical` if budget < 10%

### Edge Cases

- If total requests in the window is 0, the SLI must be reported as `1.0` (100%) — no requests means no failures
- If the actual SLI exceeds the target (performing better than SLO), remaining budget must be capped at 100%, not exceed it
- Burn rate for a window with zero budget consumed must be `0.0`, not cause division by zero
- Projected exhaustion date is `null` when burn rate ≤ 1.0 (budget is not being consumed faster than sustainable)

## Expected Functionality

- `slo_config.yaml` defines 6 SLOs across 3 services with appropriate targets and window durations
- Given an API availability SLI of 99.85% against a 99.9% target, the error budget report shows `remaining_budget_pct ≈ -50%` (budget overconsumed) and `status: "critical"`
- Given a 1h burn rate of 16× and 6h burn rate of 8×, the multi-window alerting returns `alert_type: "page"` with `severity: "critical"`
- Given a perfectly healthy service at 100% SLI, the report shows `remaining_budget_pct: 100%`, `burn_rate: 0.0`, and `status: "healthy"`
- A service with 0 total requests reports SLI as 100% and remaining budget as 100%

## Acceptance Criteria

- SLO configuration file defines 6 SLOs across 3 services with distinct SLI types, targets, and windows
- Error budget computation correctly calculates remaining budget, burn rate, and projected exhaustion date
- Multi-window burn rate alerting correctly fires page alerts (1h + 6h) and ticket alerts (6h + 3d) based on configured thresholds
- Budget report includes all required fields per SLO and correctly determines status (healthy/warning/critical) based on remaining budget
- Edge cases (zero requests, overperformance, zero burn rate) are handled without errors or incorrect results
- Tests validate SLO computation, error budget math, alerting logic, and report generation
