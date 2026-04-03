# Task: Build a DCF Valuation Engine with Monte Carlo Simulation Using QuantLib

## Background

QuantLib (https://github.com/lballabio/QuantLib) is a quantitative finance library. A new Python-based DCF (Discounted Cash Flow) valuation engine is needed that leverages QuantLib's term structure and date handling, combined with Monte Carlo simulation for uncertainty modeling. The engine must compute enterprise value, equity value per share, and confidence intervals from parameterized financial assumptions.

## Files to Create/Modify

- `Examples/python/dcf_valuation.py` (create) — Core DCF model: `DCFModel` class that projects free cash flows, computes WACC, calculates terminal value, and discounts using QuantLib's yield term structure
- `Examples/python/monte_carlo_valuation.py` (create) — Monte Carlo simulation wrapper: `MonteCarloValuation` class that runs N simulations varying revenue growth, operating margin, and discount rate, producing valuation distribution statistics
- `Examples/python/sensitivity_analysis.py` (create) — Two-variable sensitivity table: generate a matrix of enterprise values across ranges of WACC and terminal growth rate
- `Examples/python/run_valuation.py` (create) — CLI entry point that runs all three analyses for a sample company and outputs results to console and CSV files
- `Examples/python/tests/test_dcf_valuation.py` (create) — Tests for DCF math, Monte Carlo distribution properties, and sensitivity table dimensions

## Requirements

### DCF Model (`dcf_valuation.py`)

- Class `DCFModel` accepts: `base_revenue` (float), `growth_rates` (list of floats for each projection year), `operating_margin` (float), `tax_rate` (float), `capex_pct` (float, as fraction of revenue), `nwc_change_pct` (float), `wacc` (float), `terminal_growth_rate` (float), `shares_outstanding` (int), `net_debt` (float), `projection_years` (int, default 5)
- Method `project_free_cash_flows() -> list[dict]` — Returns a list of dicts per year: `{"year": n, "revenue": r, "ebit": e, "nopat": n, "fcf": f}` where FCF = NOPAT + D&A - CapEx - Delta NWC (simplified: FCF = Revenue * operating_margin * (1 - tax_rate) - Revenue * capex_pct - Revenue * nwc_change_pct)
- Method `terminal_value() -> float` — Gordon Growth Model: `FCF_last * (1 + terminal_growth_rate) / (wacc - terminal_growth_rate)`. Must raise `ValueError` if `terminal_growth_rate >= wacc`
- Method `enterprise_value() -> float` — Sum of discounted FCFs plus discounted terminal value, using discount factor `1 / (1 + wacc) ** year` for each year
- Method `equity_value_per_share() -> float` — `(enterprise_value - net_debt) / shares_outstanding`
- Use QuantLib's `Date`, `Period`, `ActualActual` day counter, and `FlatForward` yield term structure for discount factor computation instead of manual `(1+r)^n`

### Monte Carlo Simulation (`monte_carlo_valuation.py`)

- Class `MonteCarloValuation` accepts: `base_params` (dict of DCFModel parameters), `iterations` (int, default 10000), `random_seed` (int, default 42)
- Uncertain parameters with their distributions:
  - `revenue_growth_rate`: Normal(mean=base_growth, std=0.02)
  - `operating_margin`: Normal(mean=base_margin, std=0.03)
  - `wacc`: Normal(mean=base_wacc, std=0.01), clamped to [0.01, 0.30]
  - `terminal_growth_rate`: Uniform(0.01, 0.04)
- Method `run() -> dict` — Returns `{"mean": float, "median": float, "std": float, "p5": float, "p25": float, "p75": float, "p95": float, "min": float, "max": float, "values": list[float]}`
- The `wacc` sample must always be greater than the corresponding `terminal_growth_rate` sample; if not, resample
- Must use `numpy.random.Generator` with the given seed for reproducibility

### Sensitivity Analysis (`sensitivity_analysis.py`)

- Function `generate_sensitivity_table(base_params, wacc_range, tgr_range) -> pd.DataFrame` where `wacc_range` and `tgr_range` are each lists of floats
- Returns a DataFrame with WACC values as columns and terminal growth rates as the index, cells containing enterprise value
- Must skip combinations where `tgr >= wacc` and fill those cells with `NaN`

### CLI Entry Point (`run_valuation.py`)

- Define sample company: base_revenue=$500M, growth_rates=[0.12, 0.10, 0.08, 0.06, 0.05], operating_margin=0.20, tax_rate=0.25, capex_pct=0.05, nwc_change_pct=0.02, wacc=0.10, terminal_growth_rate=0.03, shares_outstanding=100_000_000, net_debt=$200M
- Print: projected FCFs, enterprise value, equity value per share
- Run Monte Carlo with 10,000 iterations, print summary statistics
- Generate sensitivity table for WACC [0.08, 0.09, 0.10, 0.11, 0.12] × TGR [0.01, 0.02, 0.03, 0.04], save to `output/sensitivity.csv`

### Expected Functionality

- DCF with the sample parameters produces an enterprise value between $1B and $3B (sanity check)
- Monte Carlo 95% confidence interval spans at least 20% of the mean (reflects meaningful uncertainty)
- Sensitivity table has 20 cells (5 WACC × 4 TGR), with NaN where TGR >= WACC
- Running `python run_valuation.py` produces console output and `output/sensitivity.csv`

## Acceptance Criteria

- All Python files run without import errors: `python -c "from dcf_valuation import DCFModel; from monte_carlo_valuation import MonteCarloValuation"`
- DCF model uses QuantLib date handling and yield term structures for discounting
- Terminal value calculation raises `ValueError` when `terminal_growth_rate >= wacc`
- Monte Carlo produces reproducible results with the same seed
- Sensitivity table correctly handles and marks invalid WACC/TGR combinations as NaN
- `cmake -DCMAKE_BUILD_TYPE=Release -B build && cmake --build build --target quantlib-test-suite` compiles QuantLib
- `python -m pytest /workspace/tests/test_creating_financial_models.py -v --tb=short` passes
