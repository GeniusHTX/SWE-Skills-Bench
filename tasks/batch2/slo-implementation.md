# Task: Add Multi-Window SLO Evaluation to the SLO Generator

## Background

The SLO Generator (https://github.com/google/slo-generator) computes SLI/SLO metrics and error budgets. New functionality is needed to support evaluating SLOs over multiple time windows simultaneously (e.g., 1-hour, 1-day, 30-day) and generating a consolidated compliance report.

## Files to Create

- `slo_generator/multi_window.py` — Multi-window SLO evaluation engine (SLI computation, per-window metrics)
- `slo_generator/burn_rate.py` — Burn rate calculation and fast-burn/slow-burn alerting logic

## Requirements

### Multi-Window Evaluation

- Accept an SLO definition that specifies multiple compliance windows (e.g., `["1h", "1d", "30d"]`)
- Compute the SLI value, error budget remaining, and burn rate for each window
- Return results as a structured report containing per-window metrics

### Error Budget Calculation

- For each window, calculate: `error_budget_remaining = 1 - (1 - SLI) / (1 - SLO_target)`
- Flag windows where the error budget is exhausted (remaining ≤ 0)
- Calculate burn rate as the ratio of error budget consumed vs. expected at the current point in the window

### Alert Conditions

- Determine whether alert conditions are met based on multi-window burn rate thresholds
- Support a fast-burn/slow-burn alerting model:
  - Fast burn: high burn rate over a short window (e.g., >14x over 1h)
  - Slow burn: elevated burn rate over a longer window (e.g., >1x over 1d)
- An alert fires only when both fast and slow burn conditions are simultaneously met

### Output

- Provide a summary indicating overall compliance status and whether alerts are active

## Expected Functionality

- Given an SLO definition and SLI data, the system evaluates compliance across all specified windows
- Error budgets and burn rates are calculated correctly for each window
- Alert conditions reflect the multi-window burn rate model

## Acceptance Criteria

- The implementation evaluates a single SLO across multiple windows and returns separate per-window results.
- Each window reports SLI, remaining error budget, and burn rate using the configured SLO target.
- Fast-burn and slow-burn alert conditions are computed and combined according to the stated alerting model.
- Exhausted error budgets are flagged clearly in the output.
- The summary indicates both overall compliance status and whether an alert should fire.
