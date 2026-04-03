# Task: Implement a Portfolio Risk Analytics Module for pyfolio

## Background

pyfolio (https://github.com/quantopian/pyfolio) is a Python library for portfolio performance and risk analysis. The project needs a new risk metrics module that computes comprehensive portfolio risk measurements including Value at Risk (VaR) using multiple methods, Conditional VaR (Expected Shortfall), risk-adjusted return ratios, drawdown analysis, and factor-based risk attribution. The module must handle real-world data issues such as missing values, non-normal return distributions, and variable-length time series.

## Files to Create/Modify

- `pyfolio/risk_metrics.py` (create) — `RiskAnalyzer` class computing VaR (historical, parametric, Cornish-Fisher), CVaR, volatility, drawdown metrics, and risk-adjusted ratios
- `pyfolio/factor_risk.py` (create) — `FactorRiskModel` class implementing factor-based risk decomposition: systematic vs idiosyncratic risk, factor exposures (beta), and marginal contribution to risk
- `pyfolio/risk_report.py` (create) — `generate_risk_report(returns, benchmark_returns, factor_returns)` function producing a structured risk summary dictionary
- `tests/test_risk_metrics.py` (create) — Tests for all risk calculations with known-answer test cases
- `tests/test_factor_risk.py` (create) — Tests for factor risk decomposition

## Requirements

### RiskAnalyzer Class

- Constructor: `RiskAnalyzer(returns: pd.Series, rf_rate: float = 0.02, annualization_factor: int = 252)`
- `returns` must be a pandas Series indexed by date; if any NaN values exist, they must be forward-filled, then any remaining NaN values at the start must be dropped
- The class must raise `ValueError` if `returns` has fewer than 30 observations after cleaning

### Volatility Metrics

- `volatility(annualized: bool = True) -> float` — Annualized standard deviation of returns; daily vol × √252
- `downside_deviation(threshold: float = 0.0, annualized: bool = True) -> float` — Standard deviation of returns below the threshold only; if no returns are below threshold, return 0.0
- `beta(market_returns: pd.Series) -> float` — Covariance of portfolio returns with market returns divided by market return variance; align dates using inner join; if fewer than 30 overlapping observations, raise `ValueError`

### Value at Risk

- `var_historical(confidence: float = 0.95) -> float` — Negative of the `(1-confidence)` percentile of returns; result is a positive number representing potential loss
- `var_parametric(confidence: float = 0.95) -> float` — `-(mean - z_score × std)` assuming normal distribution
- `var_cornish_fisher(confidence: float = 0.95) -> float` — Adjust the z-score using skewness and kurtosis: `z_cf = z + (z² - 1)×S/6 + (z³ - 3z)×K/24 - (2z³ - 5z)×S²/36` where S = skewness, K = excess kurtosis
- `cvar(confidence: float = 0.95, method: str = "historical") -> float` — Average of returns worse than VaR (Expected Shortfall); for historical method, average all returns ≤ the VaR quantile; result is a positive number

### Risk-Adjusted Returns

- `sharpe_ratio() -> float` — `(annualized_return - rf_rate) / annualized_volatility`; if volatility is 0, return 0.0
- `sortino_ratio() -> float` — `(annualized_return - rf_rate) / annualized_downside_deviation`; if downside deviation is 0, return 0.0
- `calmar_ratio() -> float` — `annualized_return / abs(max_drawdown)`; if max drawdown is 0, return 0.0
- `information_ratio(benchmark_returns: pd.Series) -> float` — `mean(excess_returns) / std(excess_returns)` where excess returns = portfolio - benchmark, annualized

### Drawdown Analysis

- `max_drawdown() -> float` — Largest peak-to-trough decline as a negative decimal (e.g., -0.25 for 25% drawdown)
- `max_drawdown_duration() -> int` — Number of trading days in the longest drawdown period (from peak to recovery)
- `drawdown_series() -> pd.Series` — Time series of drawdown at each point, calculated as `(cumulative_wealth - running_peak) / running_peak`
- `top_drawdowns(n: int = 5) -> pd.DataFrame` — Top N drawdowns by magnitude, with columns: `start_date`, `trough_date`, `end_date` (recovery), `drawdown`, `duration_days`; if fewer than N drawdowns exist, return all; drawdowns without recovery use the last date as `end_date`

### FactorRiskModel

- Constructor: `FactorRiskModel(returns: pd.Series, factor_returns: pd.DataFrame)` where `factor_returns` has columns like `market`, `size`, `value`
- `factor_exposures() -> pd.Series` — OLS regression coefficients (betas) of portfolio returns on factor returns
- `systematic_risk() -> float` — Proportion of return variance explained by factors (R² of the regression)
- `idiosyncratic_risk() -> float` — `1 - systematic_risk()`
- `marginal_contribution(factor: str) -> float` — Marginal contribution of a single factor to total portfolio variance
- The OLS regression must handle the case where factor returns have different date coverage than portfolio returns — use date intersection only

### Risk Report

- `generate_risk_report()` returns a dictionary with sections: `summary` (return/vol/Sharpe/Sortino/Calmar), `var_analysis` (all three VaR methods + CVaR at 95% and 99%), `drawdown_analysis` (max drawdown, duration, top 5), `factor_analysis` (exposures, systematic/idiosyncratic split)
- All float values must be rounded to 6 decimal places

## Expected Functionality

- Given daily returns with mean 0.05% and std 1.5%: `volatility(annualized=True)` returns approximately 23.8%
- Given a returns series where the 5th percentile is -3%: `var_historical(0.95)` returns approximately 0.03 (3% loss)
- Given a portfolio with 25% peak-to-trough decline: `max_drawdown()` returns -0.25
- Given portfolio returns and market returns: `beta()` returns the regression slope
- Given factor returns for market/size/value: `factor_exposures()` returns a Series of 3 betas
- `generate_risk_report()` returns a nested dictionary with all computed metrics

## Acceptance Criteria

- `RiskAnalyzer` computes volatility, downside deviation, and beta correctly with proper annualization
- VaR is computed using three methods (historical, parametric, Cornish-Fisher) and CVaR matches the expected shortfall definition
- Risk-adjusted ratios (Sharpe, Sortino, Calmar, Information) handle zero-denominator edge cases
- Drawdown analysis correctly identifies peak-to-trough declines, durations, and recovery dates
- `FactorRiskModel` performs OLS regression to decompose risk into systematic and idiosyncratic components
- NaN handling, date alignment, and minimum-observation requirements are enforced
- All tests pass with `pytest` using known-answer test vectors
