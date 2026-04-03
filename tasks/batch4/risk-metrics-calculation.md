# Task: Implement Portfolio Risk Metrics Engine for Pyfolio

## Background

The pyfolio library (https://github.com/quantopian/pyfolio) provides portfolio and risk analytics for financial portfolios. A new risk metrics engine is needed that calculates Value at Risk (VaR) using multiple methods, Expected Shortfall (CVaR), drawdown analysis, and risk-adjusted return ratios — all from a time series of portfolio returns, with support for rolling windows and configurable confidence levels.

## Files to Create/Modify

- `pyfolio/risk_metrics.py` (create) — `RiskEngine` class implementing VaR, CVaR, drawdowns, and risk-adjusted ratios
- `pyfolio/rolling_risk.py` (create) — Rolling-window risk calculations producing time series of risk metrics
- `tests/test_risk_metrics.py` (create) — Comprehensive tests with known-answer cases and edge conditions

## Requirements

### RiskEngine Class

- Constructor accepts: `returns` (pandas Series of period returns, indexed by date), `rf_rate` (annual risk-free rate, default 0.02), `ann_factor` (annualization factor, default 252)
- Must reject empty returns series with `ValueError`
- Must reject returns containing NaN without raising silently — require the caller to handle NaN first

### Value at Risk (VaR)

- `var_historical(confidence=0.95)` — returns the loss threshold at the given confidence level using the empirical distribution (negative of the appropriate percentile)
- `var_parametric(confidence=0.95)` — assumes normal distribution; computes VaR from mean and standard deviation using the inverse normal CDF
- `var_cornish_fisher(confidence=0.95)` — adjusts the parametric VaR for skewness and excess kurtosis using the Cornish-Fisher expansion
- All VaR methods must return a positive number representing the loss magnitude
- Confidence level must be between 0.5 and 0.999; values outside this range must raise `ValueError`

### Expected Shortfall (CVaR)

- `cvar(confidence=0.95)` — average of all losses beyond the historical VaR threshold
- Must return a value greater than or equal to VaR at the same confidence level (by definition)

### Drawdown Analysis

- `drawdowns()` — returns a pandas Series of drawdown values (negative or zero) indexed by the same dates
- `max_drawdown()` — returns the minimum value of the drawdown series (most negative point)
- `drawdown_durations()` — returns a dictionary with `"max_duration"` (int, trading days), `"avg_duration"` (float), `"num_drawdowns"` (int, count of distinct drawdown periods)
- A drawdown period starts when the drawdown series goes below zero and ends when it returns to zero

### Risk-Adjusted Return Ratios

- `sharpe_ratio()` — annualized Sharpe ratio: (annualized excess return) / (annualized volatility)
- `sortino_ratio(threshold=0.0)` — uses downside deviation (returns below threshold) as the denominator
- `calmar_ratio()` — annualized return / absolute value of max drawdown
- If volatility, downside deviation, or max drawdown is zero, the corresponding ratio must return `float('inf')` when excess return is positive, `float('-inf')` when negative, and `0.0` when zero

### Rolling Risk

- `RollingRisk` class accepting `returns`, `window` (int, trading days), `rf_rate`, `ann_factor`
- `rolling_var(confidence=0.95)` — pandas Series of historical VaR computed over a rolling window
- `rolling_sharpe()` — pandas Series of rolling annualized Sharpe ratio
- `rolling_max_drawdown()` — pandas Series of rolling max drawdown
- Rolling output must have the same index as the input returns, with NaN for the initial period shorter than the window

### Expected Functionality

- For a returns series with mean daily return 0.0005 and daily std 0.01, `var_parametric(0.95)` returns approximately 0.0115
- For a returns series where the worst 5% of returns average -0.03, `cvar(0.95)` returns approximately 0.03
- `max_drawdown()` for a portfolio that lost 20% peak-to-trough returns approximately -0.20
- `sharpe_ratio()` for a portfolio with 10% annual return, 2% risk-free, 15% annual vol returns approximately 0.533
- `sortino_ratio()` returns a higher value than `sharpe_ratio()` when downside moves account for less than half the total volatility
- Rolling VaR with a 60-day window produces NaN for the first 59 entries and valid values thereafter

## Acceptance Criteria

- VaR is computed correctly via historical, parametric, and Cornish-Fisher methods with validated confidence levels
- CVaR is always ≥ VaR at the same confidence level
- Drawdown series, max drawdown, and duration statistics are correctly derived from the cumulative return series
- Sharpe, Sortino, and Calmar ratios handle zero-denominator cases correctly
- Rolling risk calculations produce correctly windowed time series with NaN for initial incomplete windows
- Invalid inputs (empty series, NaN values, out-of-range confidence) raise `ValueError` with descriptive messages
- Tests verify correctness using synthetic returns with known statistical properties
