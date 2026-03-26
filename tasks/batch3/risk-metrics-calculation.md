# Task: Implement Portfolio Risk Metrics Module for pyfolio

## Background

pyfolio (https://github.com/quantopian/pyfolio) is a portfolio and risk analytics library for Python. The project needs a dedicated risk metrics module that computes Value at Risk (VaR), Conditional Value at Risk (CVaR), maximum drawdown analysis, and risk-adjusted return ratios from daily returns series. The module should handle realistic edge cases like short return histories, zero-variance periods, and missing data.

## Files to Create/Modify

- `pyfolio/risk_metrics.py` (create) — Risk metrics computation: VaR, CVaR, drawdowns, Sharpe, Sortino, rolling analytics
- `tests/test_risk_metrics.py` (create) — Tests covering all metrics with known inputs and edge cases

## Requirements

### Value at Risk (VaR)

- Implement **Historical VaR**: given a series of daily returns and a confidence level (e.g., 95%), return the loss threshold such that losses exceed this threshold only (1 − confidence)% of the time
- Implement **Parametric VaR**: assuming normal distribution, compute VaR as μ − z × σ where z is the z-score for the confidence level
- Both methods must accept confidence levels between 0.90 and 0.9999
- If the return series has fewer than 30 observations, raise `InsufficientDataError` with a message indicating the minimum required

### Conditional Value at Risk (CVaR / Expected Shortfall)

- Compute the average loss in the tail beyond the VaR threshold
- Support both historical (mean of returns below historical VaR) and parametric (using the normal distribution tail expectation formula)
- CVaR must always be more negative (larger magnitude) than VaR for the same confidence level; assert this invariant internally

### Maximum Drawdown Analysis

- Compute the maximum drawdown: the largest peak-to-trough decline in cumulative returns
- Return a `DrawdownResult` containing: `max_drawdown` (percentage), `peak_date`, `trough_date`, `recovery_date` (or `None` if not yet recovered), `duration_days` (peak to trough)
- Compute the top N drawdown periods (default N=5), each with their own peak/trough/recovery information, sorted by severity
- Drawdown periods must not overlap; each subsequent drawdown starts after the previous recovery (or after the previous trough if unrecovered)

### Risk-Adjusted Return Ratios

- **Sharpe Ratio**: (mean return − risk-free rate) / std(returns), annualized (multiply by √252)
- **Sortino Ratio**: (mean return − risk-free rate) / downside_deviation, annualized, where downside deviation uses only negative returns
- **Calmar Ratio**: annualized return / |max drawdown|
- Default risk-free rate is 0; accept it as an optional parameter (daily rate)
- If standard deviation or downside deviation is zero, return `float('inf')` if numerator is positive, `float('-inf')` if negative, `0.0` if both are zero

### Rolling Analytics

- Provide `rolling_var(returns, window, confidence)` — rolling VaR with a configurable window size (default: 252 trading days)
- Provide `rolling_sharpe(returns, window, risk_free_rate)` — rolling Sharpe ratio
- Rolling functions return a pandas Series aligned with the input index, with `NaN` for positions where the window is not yet full

### Expected Functionality

- For a known set of 252 daily returns with mean 0.05% and std 1%, historical VaR at 95% is approximately −1.6%
- CVaR at 95% is more negative than VaR at 95% for any return series
- A return series that drops 20% from peak and recovers reports max_drawdown ≈ 0.20
- Sharpe ratio for a series with mean daily return 0.04% and daily std 1% is approximately 1.0 annualized
- Rolling VaR with window=60 returns NaN for the first 59 positions and valid values thereafter
- A return series with only 10 observations raises `InsufficientDataError` when computing VaR

## Acceptance Criteria

- Historical and Parametric VaR produce correct values for known distributions
- CVaR is always more extreme than VaR for the same confidence level
- Maximum drawdown correctly identifies peak, trough, and recovery dates
- Top N drawdowns are non-overlapping and sorted by severity
- Sharpe, Sortino, and Calmar ratios match hand-calculated expected values within tolerance ≤ 0.001
- Rolling analytics return correctly aligned pandas Series with NaN for insufficient window periods
- `InsufficientDataError` is raised for return series shorter than the required minimum
- Zero-variance and zero-return edge cases produce the specified `inf`/`-inf`/`0.0` values
- Tests cover normal distributions, uniform distributions, single-drawdown and multi-drawdown scenarios
