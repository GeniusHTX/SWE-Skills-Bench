# Task: Build a Portfolio Risk Analytics Engine with VaR, Drawdown Analysis, and Risk-Adjusted Returns

## Background

A quantitative hedge fund needs a risk analytics engine for a multi-asset portfolio containing equities, fixed income, and commodities. The system must compute daily risk metrics (VaR, CVaR, volatility), drawdown analysis, risk-adjusted return ratios, portfolio-level risk decomposition, and generate a risk report. The engine processes daily return data for 25 assets over 3 years.

## Files to Create/Modify

- `risk/metrics.py` (create) — Core risk metric calculations: VaR (historical, parametric, Cornish-Fisher), CVaR, volatility, downside deviation
- `risk/portfolio.py` (create) — Portfolio-level risk: covariance matrix, correlation, marginal VaR, component VaR, risk contribution per asset
- `risk/drawdown.py` (create) — Drawdown analysis: max drawdown, drawdown duration, recovery time, underwater chart data
- `risk/ratios.py` (create) — Risk-adjusted returns: Sharpe, Sortino, Calmar, Information Ratio, Treynor, Omega ratio
- `risk/stress_test.py` (create) — Historical stress testing against known market events (2008 GFC, 2020 COVID, 2022 rate hike)
- `risk/report.py` (create) — Generates a structured risk report as a dict with all metrics, limits, and breaches
- `tests/test_risk_metrics.py` (create) — Unit tests for all risk calculations with known expected values

## Requirements

### Core Risk Metrics (`risk/metrics.py`)

Class `RiskMetrics`:

- `__init__(self, returns: pd.Series, risk_free_rate: float = 0.043, annualization_factor: int = 252)`.
- `annualized_volatility(self) -> float`: `returns.std() * sqrt(252)`.
- `downside_deviation(self, threshold: float = 0.0) -> float`: Std dev of returns below threshold, annualized.
- `skewness(self) -> float`: Third moment of return distribution.
- `kurtosis(self) -> float`: Excess kurtosis (fourth moment - 3).

**Value at Risk methods** (all return positive loss amount at given confidence):

- `var_historical(self, confidence: float = 0.95) -> float`: Negative of the (1-confidence) percentile of returns.
- `var_parametric(self, confidence: float = 0.95) -> float`: Assuming normal distribution: `-(mean + z_score * std)` where `z_score = norm.ppf(1 - confidence)`.
- `var_cornish_fisher(self, confidence: float = 0.95) -> float`: Cornish-Fisher expansion adjusting z-score for skewness (S) and kurtosis (K):
  ```
  z_cf = z + (z²-1)*S/6 + (z³-3z)*K/24 - (2z³-5z)*S²/36
  VaR = -(mean + z_cf * std)
  ```
- `cvar(self, confidence: float = 0.95) -> float`: Mean of returns worse than the VaR threshold (Expected Shortfall).

**Scaling:**
- `var_n_day(self, confidence: float = 0.95, days: int = 10) -> float`: Scale 1-day VaR by `sqrt(days)` (for regulatory 10-day VaR).

### Portfolio Risk (`risk/portfolio.py`)

Class `PortfolioRisk`:

- `__init__(self, returns: pd.DataFrame, weights: np.ndarray)`. Returns is T×N DataFrame (T days, N assets). Weights is N-vector summing to 1.0.
- `portfolio_return(self) -> pd.Series`: Weighted sum of asset returns per day.
- `covariance_matrix(self, method: str = "sample") -> pd.DataFrame`: Compute covariance matrix. Methods: `"sample"` (standard), `"shrinkage"` (Ledoit-Wolf shrinkage estimator).
- `correlation_matrix(self) -> pd.DataFrame`: Pairwise correlation matrix.
- `portfolio_volatility(self) -> float`: `sqrt(w^T * Σ * w) * sqrt(252)`.
- `marginal_var(self, confidence: float = 0.95) -> np.ndarray`: Partial derivative of portfolio VaR with respect to each weight.
- `component_var(self) -> pd.DataFrame`: Each asset's contribution to total portfolio VaR. Columns: `asset`, `weight`, `marginal_var`, `component_var`, `pct_contribution`. Sum of component_var equals portfolio VaR.
- `diversification_ratio(self) -> float`: Weighted average of individual volatilities / portfolio volatility. Ratio >1 indicates diversification benefit.
- `concentration_risk(self) -> dict`: Report Herfindahl index of weights, top 5 positions, and correlation of top positions.

### Drawdown Analysis (`risk/drawdown.py`)

Class `DrawdownAnalyzer`:

- `__init__(self, returns: pd.Series)`.
- `drawdown_series(self) -> pd.Series`: `(cumulative - running_max) / running_max` for each date.
- `max_drawdown(self) -> float`: Minimum value of drawdown series (most negative).
- `max_drawdown_period(self) -> dict`: Return `{"peak_date": ..., "trough_date": ..., "recovery_date": ..., "depth": ..., "duration_days": ..., "recovery_days": ...}`.
- `top_n_drawdowns(self, n: int = 5) -> list[dict]`: Identify N deepest non-overlapping drawdown periods with peak, trough, recovery dates, depth, and duration.
- `current_drawdown(self) -> dict`: Current drawdown depth and days since peak.
- `time_underwater(self) -> float`: Percentage of total days spent in drawdown (dd < 0).
- `calmar_ratio(self, years: int = 3) -> float`: Annualized return / abs(max drawdown) over specified period.

### Risk-Adjusted Ratios (`risk/ratios.py`)

Class `RiskAdjustedReturns`:

- `__init__(self, returns: pd.Series, benchmark_returns: pd.Series = None, risk_free_rate: float = 0.043)`.
- `sharpe_ratio(self) -> float`: `(annualized_return - rf) / annualized_vol`.
- `sortino_ratio(self) -> float`: `(annualized_return - rf) / downside_deviation`.
- `calmar_ratio(self) -> float`: `annualized_return / abs(max_drawdown)`.
- `information_ratio(self) -> float`: `mean(active_return) / tracking_error` where `active_return = returns - benchmark_returns` and `tracking_error = std(active_return) * sqrt(252)`. Requires benchmark.
- `treynor_ratio(self, market_returns: pd.Series) -> float`: `(annualized_return - rf) / beta`.
- `omega_ratio(self, threshold: float = 0.0) -> float`: Sum of returns above threshold / sum of returns below threshold (as absolute values).
- `annualized_return(self) -> float`: `(1 + returns).prod() ** (252/len(returns)) - 1`.

### Stress Testing (`risk/stress_test.py`)

Class `StressTest`:

- `__init__(self, returns: pd.DataFrame, weights: np.ndarray)`.
- `historical_scenarios(self) -> list[dict]`: Define market scenarios:
  - **2008 GFC** (Sep 15 - Nov 20, 2008): Equity -40%, Fixed Income +5%, Commodities -30%.
  - **2020 COVID** (Feb 19 - Mar 23, 2020): Equity -34%, Fixed Income +2%, Commodities -25%.
  - **2022 Rate Hike** (Jan 3 - Jun 16, 2022): Equity -23%, Fixed Income -12%, Commodities +15%.
  - **Risk-Off Shock**: All correlations go to 0.8, volatility doubles.
- `apply_scenario(self, scenario: dict) -> float`: Apply scenario shocks to portfolio, return portfolio loss.
- `stress_report(self) -> pd.DataFrame`: Columns: `scenario`, `portfolio_loss_pct`, `worst_asset`, `worst_asset_loss`, `recovery_estimate_days`.

### Risk Report (`risk/report.py`)

`generate_risk_report(returns: pd.DataFrame, weights: np.ndarray, benchmark: pd.Series, limits: dict) -> dict`:

- `limits` example: `{"max_var_95": 0.02, "max_drawdown": -0.15, "min_sharpe": 1.0, "max_concentration": 0.25}`.
- Report structure:
  ```python
  {
      "date": "2024-12-31",
      "portfolio_metrics": {
          "annualized_return": ...,
          "annualized_volatility": ...,
          "sharpe_ratio": ...,
          "sortino_ratio": ...,
          "max_drawdown": ...,
          "current_drawdown": ...,
      },
      "var_metrics": {
          "var_95_1d": ...,
          "var_99_1d": ...,
          "var_95_10d": ...,
          "cvar_95": ...,
          "var_method_comparison": {"historical": ..., "parametric": ..., "cornish_fisher": ...},
      },
      "risk_decomposition": {
          "component_var": [...],
          "diversification_ratio": ...,
          "top_risk_contributors": [...],  # top 5 by component VaR
      },
      "limit_breaches": [
          {"limit": "max_var_95", "current": 0.025, "limit_value": 0.02, "breach": True},
          ...
      ],
      "stress_test_results": [...],
  }
  ```

### Unit Tests (`tests/test_risk_metrics.py`)

- Test VaR historical: known returns `[-0.05, -0.03, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07]` at 90% confidence → VaR = 0.05 (negative of 10th percentile).
- Test Sharpe ratio: annualized return 12%, rf 4%, vol 15% → Sharpe ≈ 0.533.
- Test max drawdown: returns `[0.10, -0.15, -0.10, 0.05, 0.20]` → compute cumulative and verify max drawdown value.
- Test component VaR sums to approximately portfolio VaR (within 1% tolerance).
- Test diversification ratio > 1.0 for a portfolio with correlation < 1.
- Test Cornish-Fisher VaR differs from parametric when skewness and kurtosis are non-zero.
- Test CVaR >= VaR always holds.

### Expected Functionality

- `python -m risk.report --portfolio data/portfolio.csv --benchmark data/spx.csv` → outputs JSON risk report.
- Report flags `max_var_95` breach if daily 95% VaR exceeds 2% of portfolio.
- Stress test shows -18% portfolio loss under 2008 GFC scenario.
- Component VaR shows equity holdings contribute 65% of total risk.

## Acceptance Criteria

- VaR computed via 3 methods (historical, parametric, Cornish-Fisher) and CVaR as expected shortfall.
- Cornish-Fisher adjustment accounts for skewness and excess kurtosis in the return distribution.
- 10-day VaR scales 1-day VaR by `sqrt(10)` for regulatory reporting.
- Portfolio risk includes covariance matrix (sample and Ledoit-Wolf shrinkage), marginal VaR, and component VaR.
- Component VaR per asset sums to total portfolio VaR (within numerical tolerance).
- Diversification ratio measures benefit of portfolio diversification vs concentrated holdings.
- Drawdown analysis identifies top 5 non-overlapping drawdown periods with peak, trough, recovery dates.
- Risk-adjusted ratios include Sharpe, Sortino, Calmar, Information, Treynor, and Omega.
- Stress testing applies historical scenario shocks (2008, 2020, 2022) and hypothetical correlation shock.
- Risk report flags limit breaches by comparing current metrics against defined thresholds.
- Unit tests verify risk calculations against known expected values with appropriate numerical tolerances.
