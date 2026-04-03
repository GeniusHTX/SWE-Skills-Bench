# Task: Configure SLOs with Error Budget Tracking for slo-generator

## Background

slo-generator (https://github.com/google/slo-generator) is a tool for computing Service Level Indicators, Objectives, and error budgets from monitoring data. This task requires configuring SLOs for a hypothetical "payments-api" service covering availability and latency targets, implementing error budget burn-rate alerting rules, and generating an SLO compliance report.

## Files to Create/Modify

- `samples/payments-api/slo_config.yaml` (create) — SLO configuration defining two SLOs: availability (99.9%) and latency P99 < 500ms (95% of requests).
- `samples/payments-api/error_budget_policy.yaml` (create) — Error budget policy defining multi-window burn-rate alert thresholds (1h/6h fast burn, 3d/30d slow burn).
- `samples/payments-api/exporters.yaml` (create) — Exporter configuration writing SLO reports to a local JSON file.
- `samples/payments-api/slo_report_generator.py` (create) — Script that runs slo-generator with the above configs and produces a Markdown compliance report.
- `tests/test_slo_payments_api.py` (create) — Tests validating the configuration files parse correctly and the report generator produces expected output structure.

## Requirements

### SLO Definitions

- **Availability SLO**: SLI = ratio of successful responses (HTTP 2xx/3xx) to total responses. Target: 99.9% over a 30-day rolling window. Error budget: 0.1% = ~43.2 minutes of downtime per 30 days.
- **Latency SLO**: SLI = ratio of responses with latency < 500ms to total responses. Target: 95.0% over a 30-day rolling window. Error budget: 5.0%.
- Both SLOs must specify the `service_name: payments-api`, `feature_name: checkout`, and backend type `prometheus` (reading from a Prometheus-compatible data source).

### Error Budget Policy

- Define four burn-rate windows for each SLO:
  - **Fast burn (page)**: 14.4× burn rate sustained over 1 hour (checked against 5-minute window). Alert severity: critical.
  - **Fast burn (ticket)**: 6× burn rate sustained over 6 hours (checked against 30-minute window). Alert severity: warning.
  - **Slow burn (ticket)**: 3× burn rate sustained over 3 days (checked against 6-hour window). Alert severity: warning.
  - **Slow burn (report)**: 1× burn rate sustained over 30 days. Alert severity: info.
- Each alerting rule must specify the `alerting_burn_rate_threshold` and `alerting_window_seconds`.

### Report Generator

- Read the SLO config and a sample time-series data file (JSON array of `{ "timestamp", "total_requests", "successful_requests", "requests_under_500ms" }` entries).
- For each SLO, compute: current SLI value, SLO target, error budget remaining (percentage and minutes), burn rate over the last 1h and 24h.
- Output a Markdown report with:
  - Service name and reporting period.
  - Table with one row per SLO showing SLI, target, budget remaining, and status (✅ healthy / ⚠️ warning / 🔴 breached).
  - Status is `breached` if budget remaining < 0%, `warning` if < 25%, `healthy` otherwise.

### Expected Functionality

- With 100% availability data → budget remaining = 100%, status = healthy.
- With 99.85% availability over 30 days → budget remaining ≈ -50%, status = breached.
- With 96% latency compliance → budget remaining = 20% of the 5% budget (= 1% of total), status = healthy.
- With 94% latency compliance → budget remaining = negative, status = breached.

## Acceptance Criteria

- `slo_config.yaml` defines two SLOs (availability and latency) with correct targets, windows, and backend type.
- `error_budget_policy.yaml` defines four burn-rate alerting windows per SLO with correct thresholds.
- The report generator computes SLI, budget remaining, and burn rate correctly for sample data.
- The Markdown report includes a status table with per-SLO health indicators.
- Tests verify YAML parsing, SLI computation against known data, and report structure.
