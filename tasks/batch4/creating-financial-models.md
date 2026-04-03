# Task: Build a DCF Valuation Model with Sensitivity Analysis for QuantLib

## Background

The QuantLib repository (https://github.com/lballabio/QuantLib) is a quantitative finance library. A Python-based DCF (Discounted Cash Flow) valuation module is needed that can project free cash flows for a company based on historical financial data and growth assumptions, compute terminal value using both perpetuity growth and exit multiple methods, determine enterprise and equity values, and perform two-dimensional sensitivity analysis over key input variables.

## Files to Create/Modify

- `Python/examples/dcf_valuation.py` (create) — Core DCF model with cash flow projection, terminal value, and WACC calculation
- `Python/examples/sensitivity_analysis.py` (create) — Sensitivity analysis engine producing two-variable data tables and tornado charts
- `Python/examples/run_dcf_example.py` (create) — Example script demonstrating the full DCF workflow with sample company data

## Requirements

### DCF Model Class

- A `DCFModel` class accepting: `historical_revenues` (list of floats, 3–5 years), `historical_margins` (EBITDA margin per year), `capex_ratio` (capex as fraction of revenue), `nwc_change_ratio` (net working capital change as fraction of revenue change), `tax_rate` (float), `projection_years` (int, default 5)
- Growth assumptions: `revenue_growth_rates` (list of floats, one per projection year); if not provided, derive from historical CAGR
- The model must project annual Revenue, EBITDA, EBIT, Taxes, NOPAT, CapEx, Change in NWC, and Unlevered Free Cash Flow for each projection year
- All projections must be computed from formulas applied to assumptions — no hardcoded output values

### WACC Calculation

- `calculate_wacc(risk_free_rate, beta, equity_risk_premium, cost_of_debt, tax_rate, debt_ratio)` must compute the weighted average cost of capital
- Formula: WACC = E/(D+E) × cost_of_equity + D/(D+E) × cost_of_debt × (1 - tax_rate)
- Cost of equity = risk_free_rate + beta × equity_risk_premium (CAPM)
- `debt_ratio` must be between 0 and 1 (inclusive); values outside this range must raise `ValueError`

### Terminal Value

- `terminal_value_perpetuity(final_fcf, wacc, terminal_growth_rate)` — Gordon Growth Model: FCF × (1 + g) / (WACC - g)
- `terminal_value_exit_multiple(final_ebitda, exit_multiple)` — EBITDA × exit multiple
- Both must be discounted to present value
- `terminal_growth_rate` must be less than `wacc`; otherwise raise `ValueError`

### Enterprise and Equity Value

- Enterprise Value = sum of discounted projected FCFs + discounted terminal value
- Equity Value = Enterprise Value − net debt
- The model must expose `get_valuation_summary()` returning a dictionary with: `enterprise_value`, `equity_value`, `implied_share_price` (given shares outstanding), `fcf_projections` (list), `terminal_value`, `wacc`

### Sensitivity Analysis

- `SensitivityAnalysis` class accepting a `DCFModel` instance
- `two_way_table(var1_name, var1_range, var2_name, var2_range, output_metric)` — produces a 2D numpy array of `output_metric` (e.g., `"enterprise_value"`, `"equity_value"`) for all combinations of the two variables
  - Supported variables: `"wacc"`, `"terminal_growth_rate"`, `"exit_multiple"`, `"revenue_growth"` (applies uniform change to all years)
- `tornado_chart_data(variables_and_ranges, base_metric)` — for each variable, computes the metric at the low and high end (holding others at base), returning a sorted list of `(variable_name, low_value, high_value, base_value)`
- Results must be replicable: calling the same analysis with the same inputs must produce identical outputs

### Edge Cases

- A projection with all-zero revenue growth rates must produce a valid (flat) projection
- Negative revenue growth rates must be supported (declining business)
- A `terminal_growth_rate` of 0.0 must work correctly (no-growth perpetuity)
- A `debt_ratio` of 0 (all equity) must compute WACC as cost of equity
- An empty `historical_revenues` list must raise `ValueError`

### Expected Functionality

- Given 3 years of historical revenue [100M, 110M, 121M] with 5% projected growth, the model produces 5 years of FCF projections
- WACC with risk_free=0.04, beta=1.2, erp=0.06, cod=0.05, tax=0.25, debt_ratio=0.3 returns approximately 0.089
- Terminal value via perpetuity growth with FCF=15M, WACC=0.10, g=0.03 returns approximately 220.7M
- A 2-way sensitivity table varying WACC (0.08–0.12) and terminal growth (0.01–0.04) produces a matrix where enterprise value decreases as WACC increases and increases as terminal growth increases
- Tornado chart data shows that WACC and terminal growth rate are the two most impactful variables on enterprise value

## Acceptance Criteria

- The DCF model projects Revenue, EBITDA, EBIT, Taxes, NOPAT, CapEx, NWC change, and FCF for each projection year using formula-based calculations
- WACC calculation correctly applies the CAPM and weighted cost formula
- Terminal value via both perpetuity growth and exit multiple methods produces correct results
- Enterprise and equity value are correctly computed from discounted cash flows and terminal value
- Sensitivity analysis produces a valid 2D table and tornado chart data that correctly reflect variable impacts
- Invalid inputs (growth ≥ WACC for perpetuity, empty history, debt_ratio out of range) raise `ValueError` with descriptive messages
- Building/running the examples completes without errors
