# Task: Implement a Risk Metrics Library for Portfolio Analysis Using pyfolio

## Background

pyfolio (https://github.com/quantopian/pyfolio) is a performance and risk analysis library for portfolios. A new comprehensive risk metrics module is needed that computes Value at Risk (VaR), Conditional VaR (CVaR/Expected Shortfall), Sharpe and Sortino ratios, maximum drawdown analysis, and rolling risk metrics. The implementation must handle edge cases (empty series, zero volatility, insufficient data) and include a portfolio-level aggregation that combines individual asset risk into a unified report.

## Files to Create/Modify

- `pyfolio/risk_metrics.py` (create) — `RiskMetrics` class with methods for VaR, CVaR, Sharpe, Sortino, maximum drawdown, Calmar ratio, and beta/alpha calculations
- `pyfolio/rolling_risk.py` (create) — `RollingRiskAnalyzer` class that computes rolling windows of all risk metrics with configurable window sizes
- `pyfolio/portfolio_risk.py` (create) — `PortfolioRiskReport` class that combines multiple asset return series with weights, computes portfolio-level metrics, and generates a summary report
- `pyfolio/risk_report.py` (create) — Report formatter that outputs risk metrics as a formatted DataFrame, Markdown table, or dict
- `tests/test_risk_metrics_suite.py` (create) — Comprehensive tests with known-value verification for all risk calculations

## Requirements

### Core Risk Metrics (`risk_metrics.py`)

- Class `RiskMetrics` accepts: `returns` (pd.Series of periodic returns), `rf_rate` (float, annual risk-free rate, default 0.02), `trading_days` (int, default 252)
- `volatility(annualized=True) -> float` — Standard deviation of returns; if `annualized`, multiply by `sqrt(trading_days)`
- `downside_deviation(threshold=0.0, annualized=True) -> float` — Standard deviation of returns below `threshold`; returns 0.0 if no returns are below threshold
- `var_historical(confidence=0.95) -> float` — Historical VaR at given confidence level using `numpy.percentile(returns, (1 - confidence) * 100)`; returns a positive number representing loss
- `var_parametric(confidence=0.95) -> float` — Parametric VaR assuming normal distribution: `mean - z_score * std` where z_score is from `scipy.stats.norm.ppf(confidence)`
- `cvar(confidence=0.95) -> float` — Conditional VaR (Expected Shortfall): mean of returns below the VaR threshold; returns a positive number
- `sharpe_ratio() -> float` — `(annualized_return - rf_rate) / annualized_volatility`; returns 0.0 if volatility is 0
- `sortino_ratio() -> float` — `(annualized_return - rf_rate) / annualized_downside_deviation`; returns 0.0 if downside deviation is 0
- `max_drawdown() -> dict` — Returns `{"max_drawdown": float, "peak_date": Timestamp, "trough_date": Timestamp, "recovery_date": Optional[Timestamp], "duration_days": int}`; max_drawdown is a positive fraction
- `calmar_ratio() -> float` — `annualized_return / max_drawdown`; returns 0.0 if max_drawdown is 0
- `beta(benchmark_returns: pd.Series) -> float` — `Cov(asset, benchmark) / Var(benchmark)`; raises `ValueError` if series lengths don't match
- `alpha(benchmark_returns: pd.Series) -> float` — `annualized_return - (rf_rate + beta * (benchmark_annualized_return - rf_rate))` (Jensen's alpha)
- All methods must handle empty Series by raising `ValueError("Insufficient data for risk calculation")`

### Rolling Risk (`rolling_risk.py`)

- Class `RollingRiskAnalyzer` accepts: `returns` (pd.Series), `window` (int, default 63 for ~3 months), `rf_rate` (float, default 0.02)
- Method `rolling_volatility() -> pd.Series` — Rolling annualized volatility
- Method `rolling_sharpe() -> pd.Series` — Rolling Sharpe ratio
- Method `rolling_var(confidence=0.95) -> pd.Series` — Rolling historical VaR
- Method `rolling_max_drawdown() -> pd.Series` — Rolling max drawdown within each window
- All methods must return a Series of the same length as input with NaN for initial periods where the window is incomplete

### Portfolio Risk (`portfolio_risk.py`)

- Class `PortfolioRiskReport` accepts: `asset_returns` (pd.DataFrame, columns are asset names), `weights` (dict[str, float], must sum to 1.0 ± 0.001), `rf_rate` (float, default 0.02), `benchmark_returns` (Optional[pd.Series])
- Weights validation: raise `ValueError` if weights don't sum to ~1.0 or if any weight is not in [0, 1]
- Method `portfolio_returns() -> pd.Series` — Weighted sum of asset returns
- Method `summary() -> dict` — Computes all core risk metrics on portfolio returns and returns a flat dict
- Method `contribution_to_risk() -> dict[str, float]` — Marginal contribution of each asset to portfolio volatility: `weight_i * Cov(asset_i, portfolio) / portfolio_vol`
- Method `correlation_matrix() -> pd.DataFrame` — Pairwise correlation matrix of asset returns

### Expected Functionality

- For a returns series with mean daily return 0.0004 and std 0.012, annualized Sharpe ≈ `(0.0004*252 - 0.02) / (0.012*sqrt(252))` ≈ 0.42
- Historical VaR at 95% for a normal-like distribution should be approximately `mean - 1.645 * std`
- A portfolio of 60% equities / 40% bonds should have lower volatility than equities alone (diversification benefit)
- Rolling metrics with window=63 should have 62 NaN values at the start

## Acceptance Criteria

- All risk metric calculations produce correct results verified against known formulas
- VaR methods (historical and parametric) return positive loss figures
- CVaR is always >= VaR for the same confidence level
- Max drawdown correctly identifies peak, trough, and optional recovery dates
- Edge cases (empty series, zero volatility, equal returns) are handled without errors or division by zero
- Portfolio weights validation rejects invalid weights
- Contribution to risk values sum to approximately the portfolio volatility
- Rolling metrics handle window boundaries correctly with NaN padding
- `python -m pytest /workspace/tests/test_risk_metrics_calculation.py -v --tb=short` passes
