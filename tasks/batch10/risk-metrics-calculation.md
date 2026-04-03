# Task: Implement Portfolio Risk Analytics Module for pyfolio

## Background

pyfolio (https://github.com/quantopian/pyfolio) is a portfolio analytics library. The project needs a new risk metrics module that provides VaR (Value at Risk), CVaR (Conditional VaR / Expected Shortfall), risk-adjusted return ratios, drawdown analysis, rolling risk windows, and portfolio-level risk decomposition. This module will complement the existing `timeseries.py` and `tears.py` analysis, operating on pandas Series/DataFrame return data.

## Files to Create/Modify

- `pyfolio/risk_metrics.py` (new) — Core risk metric calculations: VaR (historical, parametric, Cornish-Fisher), CVaR, drawdown analysis, Sharpe/Sortino/Calmar/Omega ratios, and a summary report generator
- `pyfolio/portfolio_risk.py` (new) — Portfolio-level risk analytics: portfolio volatility, marginal/component risk contribution, correlation analysis, diversification ratio, and stress testing against historical crisis periods
- `pyfolio/rolling_risk.py` (new) — Rolling-window risk calculations: rolling volatility, rolling Sharpe, rolling VaR, rolling max drawdown, and volatility regime classification
- `tests/test_risk_metrics.py` (new) — Unit tests covering all metric calculations, edge cases, and numerical accuracy

## Requirements

### Core Risk Metrics (`risk_metrics.py`)

- Implement a `RiskMetrics` class accepting `returns: pd.Series` (periodic returns) and `rf_rate: float` (annual risk-free rate, default `0.02`), with `ann_factor: int = 252`
- Method `volatility(annualized: bool = True) -> float` — annualized standard deviation when `annualized=True`, otherwise periodic
- Method `downside_deviation(threshold: float = 0, annualized: bool = True) -> float` — standard deviation of returns below `threshold`; return `0.0` if no returns are below threshold
- Method `beta(market_returns: pd.Series) -> float` — covariance of portfolio with market divided by market variance; return `np.nan` if fewer than 2 aligned data points
- Method `var_historical(confidence: float = 0.95) -> float` — negative of the `(1-confidence)*100` percentile of returns
- Method `var_parametric(confidence: float = 0.95) -> float` — VaR assuming normal distribution using z-score
- Method `var_cornish_fisher(confidence: float = 0.95) -> float` — VaR adjusted for skewness and excess kurtosis in the return distribution
- Method `cvar(confidence: float = 0.95) -> float` — mean of returns at or below the historical VaR threshold (Expected Shortfall)
- Method `drawdowns() -> pd.Series` — series of drawdowns from cumulative peak using `(cumulative - running_max) / running_max`
- Method `max_drawdown() -> float` — minimum value from `drawdowns()`
- Method `drawdown_duration() -> dict` with keys `"max_duration"`, `"avg_duration"`, `"current_duration"` (in trading days)
- Method `sharpe_ratio() -> float` — `(annualized_mean_return - rf_rate) / annualized_volatility`; return `0` if volatility is zero
- Method `sortino_ratio() -> float` — excess return divided by annualized downside deviation; return `0` if downside deviation is zero
- Method `calmar_ratio() -> float` — annualized return divided by absolute max drawdown; return `0` if max drawdown is zero
- Method `omega_ratio(threshold: float = 0) -> float` — sum of gains above threshold divided by sum of losses below; return `np.inf` if no losses
- Method `information_ratio(benchmark_returns: pd.Series) -> float` — active return divided by tracking error
- Method `summary() -> dict[str, float]` — returns a dict containing all metrics listed above (total return, annual return, volatility, downside deviation, VaR 95/99 historical, CVaR 95, max/avg drawdown, max drawdown duration, Sharpe, Sortino, Calmar, Omega, skewness, kurtosis)

### Portfolio Risk (`portfolio_risk.py`)

- Implement a `PortfolioRisk` class accepting `returns: pd.DataFrame` (columns = assets) and `weights: pd.Series | None` (default equal-weight)
- Method `portfolio_volatility() -> float` — `sqrt(w^T * Cov * w)` annualized
- Method `marginal_risk_contribution() -> pd.Series` — `(Cov @ w) / portfolio_vol` per asset
- Method `component_risk() -> pd.Series` — `weights * marginal_risk_contribution` per asset; sum must equal `portfolio_volatility()`
- Method `diversification_ratio() -> float` — weighted average of individual asset volatilities divided by portfolio volatility; always ≥ 1.0 for a diversified portfolio
- Method `correlation_matrix() -> pd.DataFrame`
- Method `conditional_correlation(threshold_percentile: float = 10) -> pd.DataFrame` — correlation matrix computed only during periods when portfolio return is at or below the given percentile
- Method `tracking_error(benchmark_returns: pd.Series) -> float`
- Method `stress_test(scenario_returns: pd.DataFrame) -> dict[str, float]` — apply portfolio weights to scenario period returns and return `{"total_return": float, "max_drawdown": float, "worst_day": float}`

### Rolling Risk (`rolling_risk.py`)

- Implement a `RollingRiskMetrics` class accepting `returns: pd.Series` and `window: int` (default `63`, approx 3 months)
- Method `rolling_volatility(annualized: bool = True) -> pd.Series`
- Method `rolling_sharpe(rf_rate: float = 0.02) -> pd.Series`
- Method `rolling_var(confidence: float = 0.95) -> pd.Series`
- Method `rolling_max_drawdown() -> pd.Series`
- Method `volatility_regime(low_threshold: float = 0.10, high_threshold: float = 0.20) -> pd.Series` — classify each point as `"low"`, `"normal"`, or `"high"` based on rolling annualized volatility

### Expected Functionality

- `RiskMetrics` with 252 daily returns of constant 0.001 → volatility is close to `0.001 * sqrt(252)`, Sharpe is well-defined and positive, max drawdown is `0.0`
- `RiskMetrics` with an all-zeros return series → volatility is `0.0`, Sharpe is `0`, Sortino is `0`
- `var_historical(0.95)` on a return series with known 5th percentile of -0.03 → returns approximately `0.03`
- `cvar(0.95)` must always be ≥ `var_historical(0.95)` (CVaR is a more conservative measure)
- `var_cornish_fisher(0.95)` on a symmetric normal-distributed series → closely matches `var_parametric(0.95)`
- `var_cornish_fisher(0.95)` on a negatively-skewed series → higher than `var_parametric(0.95)` (accounts for tail risk)
- `drawdown_duration()` on a series with a 20-day drawdown followed by recovery → `max_duration == 20`
- `PortfolioRisk` with 2 perfectly correlated assets → `diversification_ratio() ≈ 1.0`
- `PortfolioRisk` with 2 uncorrelated assets of equal vol → `diversification_ratio() > 1.0`
- `component_risk()` values sum to `portfolio_volatility()` within floating-point tolerance
- `conditional_correlation(10)` during stress → correlation values are generally higher than unconditional correlation
- `rolling_volatility()` on 300-day series with `window=63` → returns a Series of length 300 with first 62 values as `NaN`
- `volatility_regime()` where rolling vol is 0.05 with `low_threshold=0.10` → all values are `"low"`
- `stress_test` with a scenario of 5 consecutive -5% days → `total_return < 0`, `worst_day ≈ -0.05`

## Acceptance Criteria

- `RiskMetrics.summary()` returns a dict with all specified keys and numerically correct values
- VaR: historical, parametric, and Cornish-Fisher methods are implemented and produce distinct results for non-normal distributions
- CVaR ≥ VaR at the same confidence level for any return series
- Drawdown calculations correctly identify peak-to-trough declines and their durations
- Sharpe, Sortino, Calmar, and Omega ratios handle zero-denominator cases by returning 0 or `np.inf` as specified
- `PortfolioRisk.component_risk()` sums to `portfolio_volatility()` within 1e-10 tolerance
- `RollingRiskMetrics` produces correctly-sized output Series with leading NaN values for the window warm-up period
- Volatility regime classification matches threshold logic exactly
- All tests in `tests/test_risk_metrics.py` pass via `python -m pytest tests/test_risk_metrics.py -v`
