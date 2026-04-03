# Task: Add Conditional Value at Risk and Extended Drawdown Analytics to pyfolio

## Background

pyfolio (https://github.com/quantopian/pyfolio) is a portfolio and risk analytics library for Python. The existing `timeseries.py` module computes basic risk metrics (VaR, Sharpe, max drawdown), but lacks Conditional Value at Risk (CVaR/Expected Shortfall), Sortino ratio with configurable MAR, Calmar ratio, maximum drawdown duration, and Ulcer Index calculations. The task is to extend pyfolio's risk analytics with these metrics and integrate them into the tear sheet output.

## Files to Create/Modify

- `pyfolio/risk_metrics.py` (create) — Dedicated module for advanced risk metric computations
- `pyfolio/timeseries.py` (modify) — Integrate new risk metrics into existing summary statistics functions
- `pyfolio/tears.py` (modify) — Display new risk metrics in the performance tear sheet
- `pyfolio/tests/test_risk_metrics.py` (create) — Unit tests for all new metric calculations

## Requirements

### Risk Metric Functions (`risk_metrics.py`)

All functions accept a `pd.Series` of daily returns (decimal, not percent) indexed by datetime.

#### `conditional_var(returns, confidence=0.95, method="historical")`
- Computes Conditional Value at Risk (Expected Shortfall) at the given confidence level
- `method="historical"`: Sort returns, find the VaR threshold at `(1 - confidence)` quantile, then return the mean of all returns below that threshold
- `method="gaussian"`: Compute CVaR assuming normal distribution using the formula: $CVaR = -\mu + \sigma \cdot \frac{\phi(\Phi^{-1}(1 - confidence))}{1 - confidence}$ where $\phi$ is the standard normal PDF and $\Phi^{-1}$ is the inverse CDF
- Returns a positive number representing the expected loss (e.g., 0.032 means 3.2% expected daily loss in the worst cases)

#### `sortino_ratio(returns, required_return=0.0, annualization_factor=252)`
- Computes the Sortino ratio: $(R_p - R_{MAR}) / \sigma_d$ where $\sigma_d$ is the downside deviation (standard deviation of returns below `required_return`)
- Only negative excess returns (below `required_return`) contribute to downside deviation
- Annualize both the excess return and downside deviation using the `annualization_factor`
- Return `np.inf` if downside deviation is zero and excess return is positive; return `np.nan` if both are zero

#### `calmar_ratio(returns, period=36)`
- Computes the Calmar ratio: annualized return divided by maximum drawdown over the trailing `period` months
- If `period` is `None`, use the full return series
- Return `np.nan` if max drawdown is zero

#### `max_drawdown_duration(returns)`
- Computes the duration (in calendar days) of the longest drawdown period
- A drawdown period starts when the cumulative return drops below the running peak and ends when it recovers to a new peak
- Returns a `pd.Timedelta` object
- If the series ends in a drawdown (no recovery), count the duration up to the last date

#### `ulcer_index(returns)`
- Computes the Ulcer Index: $\sqrt{\frac{1}{n} \sum_{i=1}^{n} D_i^2}$ where $D_i$ is the percentage drawdown from peak at time $i$
- Returns a float between 0 and 1

#### `omega_ratio(returns, threshold=0.0, annualization_factor=252)`
- Computes the Omega ratio: $\frac{\sum \max(R_i - threshold, 0)}{\sum \max(threshold - R_i, 0)}$
- Returns `np.inf` if the denominator is zero and numerator is positive

### Integration into `timeseries.py`

- Add calls to the new risk metric functions in the `perf_stats` function so that the statistics dictionary includes:
  - `"Conditional VaR (95%)"` — CVaR at 95% confidence
  - `"Sortino ratio"` — Sortino with MAR=0
  - `"Calmar ratio"` — Calmar over last 36 months
  - `"Max drawdown duration"` — As number of calendar days (integer)
  - `"Ulcer Index"` — Ulcer Index value
  - `"Omega ratio"` — Omega with threshold=0

### Integration into `tears.py`

- In the `create_returns_tear_sheet` function, add a new section titled `"Advanced Risk Metrics"` that displays the six new metrics in a formatted table

## Expected Functionality

- Given a return series with mean daily return 0.05% and std 1.5%:
  - `conditional_var(returns, 0.95, "historical")` returns a positive number approximately 2-4x the VaR
  - `sortino_ratio(returns)` returns a higher ratio than Sharpe when most volatility is upside
- Given a series with a 60-day drawdown followed by a 30-day drawdown:
  - `max_drawdown_duration(returns)` returns `pd.Timedelta(days=60)` corresponding to the longest drawdown
- Given a flat return series (all zeros): `sortino_ratio` returns `np.nan`, `calmar_ratio` returns `np.nan`

## Acceptance Criteria

- `conditional_var` returns correct values for both `"historical"` and `"gaussian"` methods, validated against hand-calculated examples
- `sortino_ratio` uses only downside deviation (not total standard deviation) and handles zero downside deviation correctly
- `calmar_ratio` correctly computes annualized return / max drawdown over the specified period
- `max_drawdown_duration` identifies the longest drawdown period and returns correct calendar day count, including ongoing drawdowns
- `ulcer_index` returns 0.0 for a monotonically increasing equity curve
- `omega_ratio` returns values > 1.0 for profitable strategies and < 1.0 for losing strategies
- All six metrics appear in `perf_stats` output and the returns tear sheet
- All functions handle edge cases: empty series, single-element series, constant returns
