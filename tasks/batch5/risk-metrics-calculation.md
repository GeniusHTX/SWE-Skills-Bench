# Task: Implement Portfolio Risk Metrics Module for pyfolio

## Background

pyfolio (https://github.com/quantopian/pyfolio) is a portfolio performance and risk analysis library. While it provides basic return statistics, it lacks a dedicated module for computing advanced risk metrics such as Conditional Value-at-Risk (CVaR), rolling Sortino ratio, and risk parity weights. This task requires implementing these metrics as a new module with both single-computation and rolling-window variants.

## Files to Create/Modify

- `pyfolio/risk_metrics.py` (create) — Module implementing VaR, CVaR, Sortino ratio, maximum drawdown duration, and risk parity allocation functions.
- `pyfolio/tests/test_risk_metrics.py` (create) — Tests covering each metric function with known input/output pairs, edge cases, and rolling-window variants.

## Requirements

### Value at Risk (VaR) and Conditional VaR (CVaR)

- `historical_var(returns, confidence=0.95)` — Compute VaR using the historical simulation method (percentile of return distribution). Returns a negative number representing the loss threshold.
- `parametric_var(returns, confidence=0.95)` — Compute VaR assuming normally distributed returns (mean - z_score × std).
- `historical_cvar(returns, confidence=0.95)` — Compute CVaR (Expected Shortfall): the mean of all returns below the VaR threshold.
- All functions accept a `pandas.Series` of daily returns and return a single float.

### Sortino Ratio

- `sortino_ratio(returns, target_return=0.0, annualization_factor=252)` — Compute annualized Sortino ratio: `(mean_return - target_return) × annualization_factor / downside_deviation`.
- Downside deviation considers only returns below `target_return`.
- If there are no returns below the target (all positive), return `inf`.

### Maximum Drawdown Duration

- `max_drawdown_duration(returns)` — Compute the longest period (in trading days) the portfolio spent in a drawdown before recovering to a new peak.
- Returns an integer (number of days).
- If the portfolio never recovers from its deepest drawdown (still in drawdown at series end), count through the end.

### Rolling Variants

- `rolling_var(returns, window=63, confidence=0.95)` — Rolling historical VaR with the specified window.
- `rolling_sortino(returns, window=63, target_return=0.0)` — Rolling Sortino ratio.
- Both return `pandas.Series` aligned with the input index, with `NaN` for the initial warming period.

### Risk Parity Allocation

- `risk_parity_weights(covariance_matrix)` — Given a `pandas.DataFrame` covariance matrix, compute risk parity weights where each asset contributes equally to total portfolio risk. Returns a `pandas.Series` of weights summing to 1.0.
- Use an iterative optimization approach (not a closed-form solution).

### Edge Cases

- Empty returns series → raise `ValueError` with message indicating at least 2 data points are needed.
- Single-element returns series → raise `ValueError`.
- All returns identical (zero variance) → `parametric_var` returns 0.0; `sortino_ratio` returns `inf` if mean > target.
- Covariance matrix with a zero-variance asset → `risk_parity_weights` assigns zero weight to that asset and redistributes.

### Expected Functionality

- For returns `[-0.02, -0.01, 0.01, 0.03, -0.05, 0.02, -0.03, 0.01, 0.02, -0.01]` at 95% confidence → `historical_var` ≈ -0.042, `historical_cvar` ≈ -0.05.
- For a 3-asset covariance matrix with equal variances and zero correlations → `risk_parity_weights` ≈ `[0.333, 0.333, 0.333]`.
- `max_drawdown_duration` for a returns series that drops -10% and takes 45 days to recover → returns 45.

## Acceptance Criteria

- `historical_var`, `parametric_var`, and `historical_cvar` return correct values validated against hand-computed results within a tolerance of 1e-4.
- `sortino_ratio` matches the standard formula and handles the all-positive-returns edge case.
- `max_drawdown_duration` correctly identifies the longest drawdown period, including ongoing drawdowns.
- Rolling variants produce Series of correct length with NaN in the warming period.
- `risk_parity_weights` produces weights summing to 1.0 that equalize marginal risk contributions within a tolerance of 1e-3.
- All edge cases (empty input, single element, zero variance, zero-variance asset) are handled without crashes.
- Tests pass with `pytest tests/test_risk_metrics.py`.
