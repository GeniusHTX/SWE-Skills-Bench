# Task: Build a DCF Valuation Model with Sensitivity Analysis Using QuantLib

## Background

QuantLib (https://github.com/lballabio/QuantLib) provides a comprehensive framework for quantitative finance. This task requires building a Discounted Cash Flow (DCF) valuation model in Python using QuantLib's term structure and cashflow primitives, along with a sensitivity analysis module that tests how variations in discount rate and growth rate affect the enterprise valuation.

## Files to Create/Modify

- `Examples/python/dcf_valuation.py` (create) — DCF model: projects free cash flows for 5 years, computes terminal value, discounts all cash flows using a QuantLib `YieldTermStructure`, and outputs the enterprise value.
- `Examples/python/sensitivity_analysis.py` (create) — Sensitivity analysis: varies discount rate (WACC) and revenue growth rate across defined ranges and produces a 2D sensitivity table of enterprise values.
- `Examples/python/dcf_config.py` (create) — Configuration module defining input assumptions: revenue, growth rates, EBIT margins, tax rate, capex, depreciation, working capital changes, WACC components (risk-free rate, equity risk premium, beta, debt cost, capital structure).
- `Examples/python/tests/test_dcf_valuation.py` (create) — Tests validating DCF calculations against hand-computed reference values.

## Requirements

### DCF Model

- Project free cash flows (FCF) for years 1–5 using: `FCF = EBIT × (1 - tax_rate) + depreciation - capex - Δworking_capital`.
- Revenue in each year = `base_revenue × (1 + growth_rate)^year`.
- EBIT = Revenue × EBIT margin.
- Terminal value computed using the perpetuity growth method: `TV = FCF_year5 × (1 + terminal_growth_rate) / (WACC - terminal_growth_rate)`.
- Discount each cash flow and the terminal value back to present using a QuantLib `FlatForward` yield term structure constructed from the WACC.
- Output: present value of each year's FCF, present value of terminal value, and total enterprise value.

### Sensitivity Analysis

- Vary WACC from 6% to 14% in 1% increments (9 values).
- Vary revenue growth rate from 2% to 10% in 1% increments (9 values).
- For each (WACC, growth) pair, compute the enterprise value.
- Output an 9×9 table (growth rates as rows, WACC as columns, values are enterprise value in millions).
- Highlight the cell where the base-case assumptions fall.

### Configuration

- Default assumptions: `base_revenue = 500M`, `growth_rate = 5%`, `ebit_margin = 20%`, `tax_rate = 25%`, `capex = 30M/year`, `depreciation = 20M/year`, `working_capital_change = 5M/year`, `wacc = 10%`, `terminal_growth_rate = 2.5%`.
- All parameters must be configurable via the `dcf_config.py` module; the model must not contain hardcoded financial assumptions.

### Edge Cases

- `terminal_growth_rate >= WACC` → raise a `ValueError` explaining that the perpetuity growth model is invalid.
- `wacc = 0` → raise a `ValueError` (zero discount rate).
- Negative revenue growth → the model must still compute correctly (declining revenue scenario).
- Zero capex and zero depreciation → FCF reduces to `EBIT × (1 - tax) - Δworking_capital`.

### Expected Functionality

- With default assumptions → enterprise value is approximately $753M–$760M (FCF PVs + terminal value PV).
- Sensitivity table at (WACC=10%, growth=5%) matches the default enterprise value.
- Sensitivity table at (WACC=6%, growth=10%) shows a significantly higher valuation than at (WACC=14%, growth=2%).
- Setting `terminal_growth_rate = 12%` with `wacc = 10%` → `ValueError`.

## Acceptance Criteria

- The DCF model correctly projects 5 years of free cash flows and computes terminal value using the perpetuity growth method.
- Cash flows are discounted using a QuantLib `FlatForward` term structure parameterized by WACC.
- The sensitivity analysis produces a 9×9 table of enterprise values varying WACC and growth rate.
- Edge cases (`terminal_growth_rate >= wacc`, `wacc = 0`, negative growth) are handled with appropriate errors or correct computation.
- Tests verify the enterprise value calculation against hand-computed reference values with a tolerance of ±1%.
- `cmake` build of QuantLib and `pip install -e .` of the Python bindings succeed without errors.
