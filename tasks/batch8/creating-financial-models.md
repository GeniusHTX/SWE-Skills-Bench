# Task: Build a DCF Valuation and Sensitivity Analysis Module Using QuantLib

## Background

QuantLib (https://github.com/lballabio/QuantLib) is an open-source library for quantitative finance. The project needs a Python-based financial modeling module that leverages QuantLib's term structure and discounting capabilities to build a complete Discounted Cash Flow (DCF) valuation for a company, with sensitivity analysis across key assumptions and Monte Carlo simulation for probabilistic valuation ranges.

## Files to Create/Modify

- `Examples/python/dcf_valuation.py` (create) — Complete DCF model with revenue projections, free cash flow computation, terminal value (perpetuity growth and exit multiple methods), WACC calculation, and enterprise/equity value derivation
- `Examples/python/sensitivity_analysis.py` (create) — Two-variable sensitivity tables testing impact of WACC and terminal growth rate on equity value per share, plus tornado chart data for single-variable sensitivities
- `Examples/python/monte_carlo_valuation.py` (create) — Monte Carlo simulation (10,000 iterations) sampling revenue growth, operating margin, and WACC from probability distributions to produce valuation confidence intervals
- `Examples/python/scenario_comparison.py` (create) — Bull/base/bear scenario definitions with probability weights, producing a probability-weighted expected value and scenario comparison table
- `Examples/python/financial_utils.py` (create) — Shared utility functions for WACC computation, free cash flow projection, and terminal value calculation
- `Examples/python/test_dcf.py` (create) — Test suite validating DCF math, sensitivity outputs, Monte Carlo statistics, and scenario logic

## Requirements

### DCF Model (`dcf_valuation.py`)

- Accept inputs as a dictionary: `revenue_base` (float), `revenue_growth_rates` (list of 5 yearly rates), `operating_margin` (float), `tax_rate` (float), `capex_pct_revenue` (float), `nwc_pct_revenue` (float), `depreciation_pct_revenue` (float), `terminal_growth_rate` (float), `exit_multiple` (float), `wacc` (float), `shares_outstanding` (int), `net_debt` (float)
- Project revenue for 5 years using compounding growth rates
- Compute Free Cash Flow (FCF) for each year: `EBIT × (1 - tax_rate) + depreciation - capex - Δ net_working_capital`
- Calculate terminal value using both methods:
  - Perpetuity growth: `FCF_year5 × (1 + g) / (WACC - g)`
  - Exit multiple: `EBITDA_year5 × exit_multiple`
- Discount all cash flows and terminal value to present using `WACC` as discount rate
- Compute enterprise value, subtract net debt, and derive equity value per share
- Return a structured result dictionary with yearly projections, terminal values (both methods), enterprise value, equity value, and equity value per share

### WACC Calculation (`financial_utils.py`)

- `calculate_wacc(equity_value, debt_value, cost_of_equity, cost_of_debt, tax_rate) -> float`
- `cost_of_equity` via CAPM: `risk_free_rate + beta × equity_risk_premium`
- After-tax cost of debt: `cost_of_debt × (1 - tax_rate)`
- WACC: `(E/V) × cost_of_equity + (D/V) × cost_of_debt × (1 - tax_rate)` where `V = E + D`
- If `equity_value + debt_value` is 0, raise `ValueError`

### Sensitivity Analysis (`sensitivity_analysis.py`)

- Produce a 2D sensitivity table varying `wacc` (7 values from 7% to 13% in 1% steps) and `terminal_growth_rate` (5 values from 1% to 3% in 0.5% steps), computing equity value per share for each combination (35 cells total)
- Produce tornado chart data: for each of 6 input variables (`revenue_growth`, `operating_margin`, `tax_rate`, `wacc`, `terminal_growth_rate`, `exit_multiple`), compute equity value at ±20% of base case, sorted by absolute impact descending
- Return both tables as nested lists/dictionaries suitable for tabular display

### Monte Carlo Simulation (`monte_carlo_valuation.py`)

- Run 10,000 iterations sampling:
  - `revenue_growth_rates[0]`: normal distribution with mean = base case, std = 3%
  - `operating_margin`: triangular distribution (min = base - 5%, mode = base, max = base + 3%)
  - `wacc`: uniform distribution (base - 2%, base + 2%)
- For each iteration, run the full DCF and record equity value per share
- Return: mean, median, standard deviation, 5th/25th/75th/95th percentiles, probability of value > base case value, probability of value < 0
- Set random seed for reproducibility: `numpy.random.seed(42)`

### Scenario Comparison (`scenario_comparison.py`)

- Define three scenarios with overrides on `revenue_growth_rates`, `operating_margin`, and `terminal_growth_rate`:
  - **Bull** (25% probability): higher growth, wider margins
  - **Base** (50% probability): input assumptions as-is
  - **Bear** (25% probability): lower growth, compressed margins
- Compute DCF for each scenario and produce:
  - Per-scenario equity value per share
  - Probability-weighted expected value: `Σ(probability × equity_value)`
  - Range: `[bear_value, bull_value]`

### Edge Cases

- If `terminal_growth_rate >= wacc`, the perpetuity growth terminal value is undefined — raise `ValueError("Terminal growth rate must be less than WACC")`
- If any `revenue_growth_rate` results in negative revenue, clamp revenue at 0
- Monte Carlo iterations producing negative equity values (debt > enterprise value) must be recorded as 0 for per-share value, not negative
- If `shares_outstanding` is 0, raise `ValueError`

## Expected Functionality

- Given a company with $100M base revenue, 5% annual growth, 20% operating margin, 10% WACC, and 2% terminal growth: the DCF produces an enterprise value and equity value per share
- The sensitivity table shows equity value per share increasing as WACC decreases and terminal growth increases
- The tornado chart shows that WACC and operating margin are the most impactful variables (highest absolute sensitivity)
- The Monte Carlo simulation with seed=42 produces a distribution where the median is close to the base case DCF value
- The scenario comparison shows bull > base > bear equity values with the weighted expected value between base and bull

## Acceptance Criteria

- The DCF model correctly projects 5-year cash flows, computes terminal value (both methods), discounts to present, and derives equity value per share
- WACC calculation follows the CAPM framework and handles edge cases (zero total value)
- Sensitivity analysis produces a 7×5 WACC-vs-growth table and tornado chart data for 6 variables
- Monte Carlo simulation runs 10,000 iterations with reproducible results and produces distribution statistics including percentiles and probabilities
- Scenario comparison computes per-scenario DCF values and probability-weighted expected value
- Invalid inputs (growth ≥ WACC, zero shares, zero capital structure) raise descriptive `ValueError` exceptions
- All tests pass with `pytest`
