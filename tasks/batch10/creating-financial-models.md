# Task: Implement DCF Valuation Engine and Monte Carlo Simulator for QuantLib

## Background

QuantLib (https://github.com/lballabio/QuantLib) is a C++ library for quantitative finance. The project needs a new Python-based financial modeling layer that provides Discounted Cash Flow (DCF) valuation and Monte Carlo simulation for equity valuation. This layer will consume QuantLib's term structure and instrument infrastructure while implementing projection, discounting, and stochastic simulation logic in Python modules alongside the existing C++ source.

## Files to Create/Modify

- `ql/python/dcf_valuation.py` (new) — DCF model engine computing free cash flow projections, terminal value (perpetuity growth and exit multiple methods), WACC, and enterprise/equity value
- `ql/python/monte_carlo_valuation.py` (new) — Monte Carlo simulation engine with configurable probability distributions for revenue growth, margins, and discount rates; outputs confidence intervals and probability-weighted valuations
- `ql/python/sensitivity.py` (new) — Two-variable sensitivity analysis generating data tables showing valuation across ranges of input assumptions
- `ql/python/test_financial_models.py` (new) — Unit tests covering DCF calculations, Monte Carlo statistical properties, sensitivity table correctness, and edge cases

## Requirements

### DCF Valuation Engine (`dcf_valuation.py`)

- Implement a `DCFModel` class that accepts:
  - `revenue_base: float` — most recent annual revenue
  - `revenue_growth_rates: list[float]` — projected annual growth rates for the explicit forecast period (e.g., `[0.15, 0.12, 0.10, 0.08, 0.06]` for 5 years)
  - `operating_margin: float` — projected EBIT margin
  - `tax_rate: float` — corporate tax rate
  - `capex_pct_revenue: float` — capital expenditure as percentage of revenue
  - `nwc_pct_revenue: float` — net working capital change as percentage of revenue
  - `depreciation_pct_revenue: float` — depreciation as percentage of revenue
  - `wacc: float` — weighted average cost of capital
  - `terminal_growth_rate: float` — perpetuity growth rate for terminal value
  - `exit_multiple: float | None` — optional EV/EBITDA exit multiple for terminal value
  - `shares_outstanding: float` — number of shares for per-share value
  - `net_debt: float` — net debt to subtract from enterprise value
- Method `project_cash_flows() -> list[dict]` must return a list of dicts with keys: `year`, `revenue`, `ebit`, `nopat`, `depreciation`, `capex`, `nwc_change`, `fcf` for each forecast year
- Method `terminal_value_perpetuity() -> float` must compute terminal value as `fcf_last * (1 + terminal_growth_rate) / (wacc - terminal_growth_rate)`
- Method `terminal_value_exit_multiple() -> float | None` must compute terminal value as `ebitda_last * exit_multiple` if `exit_multiple` is provided, else return `None`
- Method `enterprise_value(method: str = "perpetuity") -> float` must discount all projected FCFs and the terminal value back to present using WACC
- Method `equity_value(method: str = "perpetuity") -> float` must return `enterprise_value - net_debt`
- Method `price_per_share(method: str = "perpetuity") -> float` must return `equity_value / shares_outstanding`
- Raise `ValueError` if `wacc <= terminal_growth_rate` (Gordon Growth Model constraint)
- Raise `ValueError` if `revenue_base <= 0` or `shares_outstanding <= 0`

### Monte Carlo Simulation (`monte_carlo_valuation.py`)

- Implement a `MonteCarloValuation` class that accepts a base `DCFModel` instance and a `simulations: int` parameter (default `5000`)
- Accept distribution parameters as dicts:
  - `growth_distribution: dict` with keys `type` (`"normal"` or `"triangular"`), `mean`, `std` (for normal) or `low`, `mode`, `high` (for triangular)
  - `margin_distribution: dict` with same structure
  - `wacc_distribution: dict` with same structure
- Method `run() -> MonteCarloResult` must execute `simulations` iterations, each time sampling growth rate, margin, and WACC from their distributions, constructing a `DCFModel`, and recording the resulting equity value
- `MonteCarloResult` dataclass must contain: `values: list[float]`, `mean: float`, `median: float`, `std: float`, `percentile_5: float`, `percentile_25: float`, `percentile_75: float`, `percentile_95: float`, `probability_above_zero: float`
- If a sampled WACC is ≤ sampled terminal growth rate, that iteration must be skipped (not counted) and logged
- Results must be reproducible when a `random_seed: int` is provided

### Sensitivity Analysis (`sensitivity.py`)

- Implement a `SensitivityAnalyzer` class that accepts a base `DCFModel` instance
- Method `two_way_table(param_x: str, range_x: list[float], param_y: str, range_y: list[float], output_metric: str = "equity_value") -> dict` must return a dict containing:
  - `row_param`: name of Y parameter
  - `col_param`: name of X parameter
  - `row_values`: the Y range
  - `col_values`: the X range
  - `table`: 2D list of `output_metric` values (rows correspond to Y values, columns to X values)
- Supported parameters: `"wacc"`, `"terminal_growth_rate"`, `"operating_margin"`, `"revenue_growth"` (applies uniform override to all years)
- Supported output metrics: `"enterprise_value"`, `"equity_value"`, `"price_per_share"`
- Method `tornado_chart(params: dict[str, tuple[float, float]], output_metric: str = "equity_value") -> list[dict]` must return a list sorted by impact magnitude (descending), each dict containing: `param`, `low_value`, `high_value`, `low_result`, `high_result`, `spread`
- Raise `ValueError` for unsupported parameter names or output metrics

### Expected Functionality

- `DCFModel` with `revenue_base=1000`, `growth_rates=[0.10]*5`, `operating_margin=0.20`, `tax_rate=0.25`, `wacc=0.10`, `terminal_growth_rate=0.03` → `enterprise_value()` returns a positive float; each projected year's revenue = previous × (1 + growth_rate)
- `DCFModel` with `wacc=0.05`, `terminal_growth_rate=0.06` → raises `ValueError`
- `DCFModel` with `revenue_base=-100` → raises `ValueError`
- `terminal_value_exit_multiple()` with `exit_multiple=None` → returns `None`
- `terminal_value_exit_multiple()` with `exit_multiple=12.0` → returns `ebitda_last * 12.0`
- `MonteCarloValuation` with `simulations=10000` and `random_seed=42` → two runs produce identical `mean` and `percentile_95` values
- `MonteCarloValuation` where `wacc_distribution` samples occasionally produce wacc ≤ terminal_growth_rate → those iterations are skipped; `len(result.values) < simulations`
- `SensitivityAnalyzer.two_way_table(param_x="wacc", range_x=[0.08, 0.10, 0.12], param_y="terminal_growth_rate", range_y=[0.02, 0.03, 0.04])` → returns 3×3 table where increasing WACC decreases values and increasing growth rate increases values
- `tornado_chart` with `{"wacc": (0.08, 0.12), "operating_margin": (0.15, 0.25)}` → returns list sorted by spread magnitude
- `two_way_table` with `param_x="invalid_param"` → raises `ValueError`

## Acceptance Criteria

- `DCFModel` produces correct free cash flow projections, terminal values, and enterprise/equity values for known inputs
- Terminal value via perpetuity growth and exit multiple methods are both implemented and selectable
- `ValueError` is raised for invalid inputs (wacc ≤ growth rate, negative revenue, zero shares)
- Monte Carlo simulation produces statistically valid distributions with correct confidence intervals
- Monte Carlo results are reproducible with the same random seed
- Iterations with invalid parameter combinations (wacc ≤ growth) are skipped gracefully
- Sensitivity analysis generates correct two-way tables where monotonic relationships hold (higher WACC → lower value)
- Tornado chart entries are sorted by impact spread in descending order
- The C++ project builds successfully via `cmake --build build`
- All tests in `ql/python/test_financial_models.py` pass via `python -m pytest ql/python/test_financial_models.py -v`
