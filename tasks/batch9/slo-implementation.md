# Task: Build an SLO Framework with Error Budgets and Multi-Window Burn Rate Alerting

## Background

The SLO Generator (https://github.com/google/slo-generator) computes SLO metrics. A new Python module is needed that defines SLIs and SLOs declaratively from YAML, computes compliance over rolling windows, calculates error budgets, implements multi-window multi-burn-rate alerting (Google SRE book approach), and generates SLO reports with recommendations.

## Files to Create/Modify

- `slo_framework/models.py` (create) — Pydantic models: `SLIDefinition`, `SLODefinition`, `ErrorBudget`, `BurnRateAlert`, `SLOReport`
- `slo_framework/calculator.py` (create) — `SLOCalculator` class that computes SLI values, SLO compliance, error budget remaining, and burn rates from time-series data
- `slo_framework/alerting.py` (create) — `BurnRateAlerter` class implementing multi-window multi-burn-rate alerting with configurable thresholds per Google SRE recommendations
- `slo_framework/config.py` (create) — YAML config loader that parses SLO definitions from config files with validation
- `slo_framework/reporter.py` (create) — `SLOReporter` that generates Markdown and JSON reports with compliance status, remaining budget, and recommendations
- `slo_framework/prometheus.py` (create) — PromQL query generator for common SLI patterns (availability, latency, throughput) and recording/alerting rules
- `tests/test_slo_framework.py` (create) — Tests with known time-series data and expected SLO computations

## Requirements

### Models (`models.py`)

- `SLIDefinition`: `name` (str), `type` (Literal["availability", "latency", "throughput"]), `description` (str), `good_events_query` (str, PromQL), `total_events_query` (str, PromQL), `threshold` (Optional[float], for latency SLIs)
- `SLODefinition`: `name` (str), `sli` (SLIDefinition), `target` (float, e.g., 0.999), `window` (str, e.g., "28d"), `alert_burn_rates` (list[BurnRateConfig])
- `BurnRateConfig`: `severity` (str: "critical", "warning", "ticket"), `long_window` (str), `short_window` (str), `burn_rate_threshold` (float)
  - Default configs per Google SRE: critical (1h/5m, burn=14.4), warning (6h/30m, burn=6), ticket (3d/6h, burn=1)
- `ErrorBudget`: `total_budget` (float), `consumed` (float), `remaining` (float), `remaining_percent` (float), `estimated_exhaustion_hours` (Optional[float])
- `SLOReport`: `slo_name`, `window`, `target`, `current_sli`, `compliance` (bool), `error_budget` (ErrorBudget), `active_alerts` (list), `recommendation` (str)

### SLO Calculator (`calculator.py`)

- Class `SLOCalculator`:
- Method `compute_sli(good_events: int, total_events: int) -> float`:
  - Returns `good_events / total_events` if total > 0, else 1.0 (no events = no failures)
- Method `compute_error_budget(sli_value: float, target: float, window_seconds: int) -> ErrorBudget`:
  - `total_budget = (1 - target) * window_seconds` (in error-seconds)
  - `consumed = (1 - sli_value) * window_seconds`
  - `remaining = total_budget - consumed`
  - `remaining_percent = (remaining / total_budget) * 100` (clamped to [0, 100])
  - `estimated_exhaustion_hours`: if current burn rate > 0, `remaining / current_rate / 3600`, else None
- Method `compute_burn_rate(short_window_error_rate: float, target: float) -> float`:
  - `burn_rate = short_window_error_rate / (1 - target)`
  - A burn rate of 1.0 means budget consumed at exactly the allowed rate
  - A burn rate > 1.0 means budget is being consumed faster than allowed
- Method `evaluate_slo(good_counts: list[int], total_counts: list[int], target: float, window_seconds: int) -> SLOReport`:
  - Computes aggregate SLI over the full window
  - Computes error budget
  - Returns SLOReport with compliance flag (`sli_value >= target`)

### Burn Rate Alerter (`alerting.py`)

- Class `BurnRateAlerter`:
- Constructor accepts `slo: SLODefinition`
- Method `evaluate(long_window_error_rate: float, short_window_error_rate: float, config: BurnRateConfig) -> Optional[BurnRateAlert]`:
  - Alert fires if BOTH conditions are true:
    1. `long_window_error_rate / (1 - slo.target) >= config.burn_rate_threshold`
    2. `short_window_error_rate / (1 - slo.target) >= config.burn_rate_threshold`
  - Returns `BurnRateAlert(severity=config.severity, long_burn_rate, short_burn_rate, threshold)` or None
- Method `evaluate_all(error_rates: dict[str, float]) -> list[BurnRateAlert]`:
  - `error_rates` keys: "1h", "5m", "6h", "30m", "3d", "6h_short"
  - Evaluates all configured burn rate windows
  - Returns all firing alerts sorted by severity (critical first)
- Default thresholds:
  - Critical: 1h/5m windows, threshold 14.4 (budget exhausted in 2h at this rate)
  - Warning: 6h/30m windows, threshold 6.0 (budget exhausted in ~5h)
  - Ticket: 3d/6h windows, threshold 1.0 (budget being consumed)

### PromQL Generator (`prometheus.py`)

- Function `availability_sli_queries(service: str, namespace: str) -> tuple[str, str]` — Returns (good_query, total_query):
  - Good: `sum(rate(http_requests_total{service="<service>", namespace="<namespace>", status!~"5.."}[<window>]))`
  - Total: `sum(rate(http_requests_total{service="<service>", namespace="<namespace>"}[<window>]))`
- Function `latency_sli_queries(service, namespace, threshold_ms: float) -> tuple[str, str]`:
  - Good: `sum(rate(http_request_duration_seconds_bucket{..., le="<threshold_ms/1000>"}[<window>]))`
  - Total: `sum(rate(http_request_duration_seconds_count{...}[<window>]))`
- Function `generate_recording_rules(slo: SLODefinition) -> list[dict]` — Generates Prometheus recording rules:
  - `slo:sli_ratio:rate<window>` for each relevant window (5m, 30m, 1h, 6h, 3d, 28d)
- Function `generate_alerting_rules(slo: SLODefinition) -> list[dict]` — Generates multi-window burn rate alert rules:
  - One alert rule per burn rate config with both long and short window conditions in `expr`

### Reporter (`reporter.py`)

- Method `to_markdown(reports: list[SLOReport]) -> str`:
  - Summary table: SLO name, target, current, compliance (✅/❌), budget remaining %
  - Detail sections per SLO with error budget, active alerts, and recommendations
- Method `to_json(reports: list[SLOReport]) -> str` — JSON-serialized reports
- Recommendations based on budget:
  - Remaining > 50%: "Budget healthy. Safe to deploy changes."
  - Remaining 25-50%: "Budget moderate. Proceed with caution on risky changes."
  - Remaining 0-25%: "Budget low. Freeze non-critical deployments."
  - Remaining <= 0%: "Budget exhausted. Stop all deployments and focus on reliability."

### Expected Functionality

- An SLO with target 99.9% and SLI of 99.85% has compliance=False, budget consumed at ~150% of allowed rate
- Burn rate of 14.4 with 99.9% target means error rate is `14.4 * 0.001 = 1.44%` — critical alert fires
- Error budget for 99.9% target over 28 days: total budget = 2419.2 error-seconds (28 * 86400 * 0.001)
- PromQL generator produces valid query strings with proper label selectors

## Acceptance Criteria

- SLI computation handles edge case of zero total events (returns 1.0)
- Error budget calculation correctly computes remaining percentage clamped to [0, 100]
- Burn rate alerting requires BOTH long and short window conditions to fire (multi-window)
- Alert severities follow Google SRE recommendations: critical (14.4x), warning (6x), ticket (1x)
- PromQL queries use correct Prometheus metric names and label selectors
- Recording rules cover all required windows (5m through 28d)
- Report recommendations correctly tier based on remaining budget percentage
- `python -m pytest /workspace/tests/test_slo_implementation.py -v --tb=short` passes
