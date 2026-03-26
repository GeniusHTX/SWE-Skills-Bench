# Task: Implement SLO Configuration and Burn Rate Alert Engine for slo-generator

## Background

The slo-generator project (https://github.com/google/slo-generator) is a tool for computing SLI/SLO metrics and generating error budget reports. The project needs a new SLO configuration engine that supports multi-window burn rate alerting, error budget tracking, and configurable alerting thresholds. This should integrate with the existing `slo_generator` Python package structure.

## Files to Create/Modify

- `slo_generator/burn_rate.py` (create) — Multi-window burn rate calculator and alert evaluator
- `slo_generator/error_budget.py` (create) — Error budget tracker with remaining budget, consumption rate, and projected exhaustion
- `slo_generator/slo_config_validator.py` (create) — SLO configuration schema validation
- `tests/unit/test_burn_rate.py` (create) — Tests for burn rate calculations and alert evaluation
- `tests/unit/test_error_budget.py` (create) — Tests for error budget tracking

## Requirements

### SLO Configuration Validation

- Define an SLO configuration schema with fields: `name` (str, required), `description` (str), `service` (str, required), `sli_type` (one of `"availability"`, `"latency"`, `"throughput"`, `"quality"`), `target` (float, must be between 0.0 and 1.0 exclusive), `window` (one of `"rolling_7d"`, `"rolling_28d"`, `"rolling_30d"`, `"calendar_month"`), `alert_policies` (list of alert policy configs)
- Validate that `target` is realistic: for availability SLIs, target must be ≥ 0.9; for latency, target must be ≥ 0.5
- Raise `SLOConfigError` with specific messages for each validation failure
- Support loading configuration from a dict or YAML string

### Burn Rate Calculation

- Implement a `BurnRateCalculator` class accepting an SLO target and a time series of good/total event counts
- Burn rate = (error_rate / error_budget_rate) where error_budget_rate = 1 − target
- Support multi-window burn rate: compute burn rate for short window (e.g., 5m) and long window (e.g., 1h) simultaneously
- The short window burn rate captures sudden spikes; the long window prevents false positives from brief anomalies

### Alert Policies

- An alert fires when BOTH the short-window and long-window burn rates exceed their respective thresholds
- Support predefined alert severity levels with recommended window/threshold pairs:
  - `critical`: short_window=5min, long_window=1h, burn_rate_threshold=14.4
  - `warning`: short_window=30min, long_window=6h, burn_rate_threshold=6.0
  - `ticket`: short_window=2h, long_window=1d, burn_rate_threshold=3.0
- Custom alert policies can override any of these values
- `evaluate_alerts(good_events, total_events, timestamps)` returns a list of fired alerts, each with severity, current burn rates, and window details

### Error Budget Tracking

- Implement an `ErrorBudgetTracker` class that tracks error budget over a specified window
- Given an SLO target of 99.9% and a 30-day window, the error budget is 0.1% × 30 days = 43.2 minutes of downtime
- Track: `total_budget` (in the same unit as input: events or time), `consumed_budget`, `remaining_budget`, `remaining_percentage`
- Calculate `consumption_rate` — the rate at which budget is being consumed per hour over the last N hours
- Project `exhaustion_date` — the date at which remaining budget will reach zero at the current consumption rate; return `None` if consumption rate is zero or negative (budget is being recovered)

### Expected Functionality

- An SLO with target 0.999 over 30 days has error_budget = 0.001 × 30 × 24 × 60 = 43.2 minutes
- If 20 minutes of budget consumed, remaining_percentage = (43.2 − 20) / 43.2 ≈ 53.7%
- A 5-minute window with error_rate = 1.44% and target 0.999 (budget_rate = 0.1%) has burn_rate = 14.4, triggering critical alert
- If only the 5-minute window exceeds threshold but the 1-hour window does not, no alert fires (both windows must exceed)
- Config with target = 1.0 raises `SLOConfigError` (target must be less than 1.0)
- Config with sli_type = "availability" and target = 0.5 raises `SLOConfigError` (too low for availability)

## Acceptance Criteria

- SLO configuration validates all fields and raises `SLOConfigError` with specific messages for violations
- Burn rate is calculated correctly as error_rate / error_budget_rate
- Multi-window alerts fire only when both short and long windows exceed thresholds
- Predefined severity levels (critical/warning/ticket) use the correct window sizes and burn rate thresholds
- Error budget tracker computes total, consumed, and remaining budget correctly
- Consumption rate and exhaustion date projection are accurate
- Exhaustion date is `None` when consumption rate is zero or negative
- Tests cover normal SLO operations, boundary conditions, alert firing/not-firing scenarios, and configuration validation errors
