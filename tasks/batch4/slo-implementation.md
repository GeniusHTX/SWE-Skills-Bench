# Task: Implement an SLO Framework with SLI Computation, Error Budgets, and Burn-Rate Alerts

## Background

The slo-generator repository (https://github.com/google/slo-generator) computes SLO achievement from monitoring data. A new Python module is needed that defines SLIs (Service Level Indicators) for availability and latency, computes SLO achievement over rolling windows, tracks error budget consumption, implements multi-window burn-rate alerting, and generates SLO status reports — following Google SRE best practices.

## Files to Create/Modify

- `slo_generator/sli.py` (create) — SLI definitions and computation for availability and latency indicators
- `slo_generator/slo.py` (create) — SLO tracking with rolling window achievement and error budget calculation
- `slo_generator/burn_rate.py` (create) — Multi-window burn-rate alert evaluation
- `slo_generator/report.py` (create) — SLO status report generator with budget projections
- `tests/test_slo_implementation.py` (create) — Tests for SLI computation, SLO tracking, burn-rate alerts, and reporting

## Requirements

### SLI Definitions (sli.py)

- `AvailabilitySLI` class: computes good events / total events
  - Constructor accepts: `good_events` (int), `total_events` (int)
  - `value() -> float` — returns the ratio (0.0–1.0)
  - Raises `ValueError` if `total_events` is 0 or negative, or if `good_events > total_events`
- `LatencySLI` class: computes fraction of requests below a latency threshold
  - Constructor accepts: `latencies` (list of floats in seconds), `threshold` (float in seconds)
  - `value() -> float` — returns fraction of latencies ≤ threshold
  - Raises `ValueError` if `latencies` is empty or `threshold` is negative
- `from_prometheus(metric_name, query_result) -> SLI` — factory function that creates the appropriate SLI from a Prometheus query result dict with keys `"good"`, `"total"` (for availability) or `"latencies"`, `"threshold"` (for latency)

### SLO Tracking (slo.py)

- `SLO` class accepting: `name` (str), `target` (float, e.g., 0.999), `window_days` (int, default 28), `sli_type` (str, one of `"availability"`, `"latency"`)
- `record(timestamp: datetime, sli_value: float)` — records a measurement at the given timestamp
- `achievement(at: datetime = None) -> float` — computes the SLO achievement over the rolling window ending at `at` (or now); returns the average SLI value over the window
- `error_budget_total() -> float` — returns `1.0 - target` (e.g., 0.001 for 99.9%)
- `error_budget_remaining(at: datetime = None) -> float` — returns `error_budget_total - (1.0 - achievement)`; negative means budget exhausted
- `error_budget_remaining_percent(at: datetime = None) -> float` — remaining budget as a percentage (0–100) of total budget
- `is_met(at: datetime = None) -> bool` — returns True if achievement ≥ target

### Burn-Rate Alerting (burn_rate.py)

- `BurnRateAlert` class accepting: `slo` (SLO), `long_window_minutes` (int), `short_window_minutes` (int), `burn_rate_threshold` (float)
- `evaluate(at: datetime = None) -> AlertResult` — computes burn rate over both windows and fires if both exceed the threshold
- `AlertResult` fields: `firing` (bool), `long_window_burn_rate` (float), `short_window_burn_rate` (float), `severity` (str)
- Burn rate = (1 - achievement_over_window) / (1 - slo_target)
- Standard multi-window configuration:
  - Page (critical): long 1h, short 5m, threshold 14.4
  - Page (high): long 6h, short 30m, threshold 6.0
  - Ticket (medium): long 3d, short 6h, threshold 1.0
- `MultiWindowBurnRate` class accepting an `SLO` and creating all three standard alert levels, with `evaluate_all(at) -> list[AlertResult]`

### Report Generator (report.py)

- `SLOReport` class accepting a list of `SLO` instances
- `generate(at: datetime = None) -> dict` — produces:
  - `"summary"`: list of per-SLO dicts with `name`, `target`, `achievement`, `error_budget_remaining_percent`, `status` ("met"/"violated")
  - `"budget_forecast"`: for each SLO, projected days until budget exhaustion at current burn rate (or "N/A" if within budget)
  - `"alerts"`: list of currently firing burn-rate alerts across all SLOs
  - `"generated_at"`: ISO-8601 timestamp
- `to_markdown() -> str` — renders the report as a markdown table

### Expected Functionality

- `AvailabilitySLI(good_events=999, total_events=1000).value()` returns 0.999
- `LatencySLI(latencies=[0.1, 0.2, 0.5, 1.0], threshold=0.5).value()` returns 0.75
- An SLO with target 0.999 and achievement 0.998 has `error_budget_remaining_percent ≈ 0%` (budget nearly exhausted)
- A burn rate of 14.4× on the 1-hour window means the error budget would be consumed in ~5 hours at current rate
- The report shows all SLOs with their status and projected budget exhaustion dates

## Acceptance Criteria

- SLI classes correctly compute availability and latency indicators with input validation
- SLO tracks measurements over a rolling window and computes achievement, error budget, and budget remaining
- Burn-rate alerts correctly evaluate against multi-window thresholds and fire at appropriate severity levels
- Report generator produces a structured summary with budget forecasts and active alerts
- Edge cases (zero events, empty latencies, budget exhaustion, 100% achievement) are handled correctly
- Tests verify SLI computation, SLO window tracking, burn-rate math, and report generation
