# Task: Build a DCF Valuation Model with Monte Carlo Simulation for a SaaS Company

## Background

A growth-stage SaaS company (CloudMetrics Inc.) needs a complete financial model for a potential Series C fundraise. The model must include a 5-year DCF valuation with two terminal value methods, a sensitivity analysis on key drivers (revenue growth and WACC), and a Monte Carlo simulation (5,000 iterations) to produce a probability-weighted valuation range. Historical financials for FY2021-FY2024 are provided as inputs.

## Files to Create/Modify

- `models/dcf_model.py` (create) — DCF valuation engine: projects 5-year free cash flows, computes WACC, terminal value (perpetuity growth + exit multiple), enterprise value, and equity value
- `models/monte_carlo.py` (create) — Monte Carlo simulation: runs 5,000 iterations sampling from probability distributions for revenue growth, operating margin, WACC, and terminal growth rate; outputs statistics and confidence intervals
- `models/sensitivity.py` (create) — Two-way sensitivity analysis generating data tables for revenue growth × WACC and revenue growth × exit multiple combinations
- `models/scenario_analysis.py` (create) — Three scenarios (bull/base/bear) with probability weights and expected value computation
- `models/inputs.py` (create) — All input assumptions and historical financials as structured data
- `models/output_report.py` (create) — Generates a summary report with valuation ranges, key metrics, and scenario comparisons
- `tests/test_dcf.py` (create) — Unit tests for DCF calculations, WACC computation, and terminal value methods

## Requirements

### Historical Financials (`models/inputs.py`)

CloudMetrics Inc. historical data:

```python
historical = {
    "revenue": {2021: 12_000_000, 2022: 19_200_000, 2023: 28_800_000, 2024: 40_320_000},
    "cogs": {2021: 3_600_000, 2022: 5_376_000, 2023: 7_776_000, 2024: 10_483_200},
    "opex": {2021: 10_800_000, 2022: 15_360_000, 2023: 20_160_000, 2024: 24_192_000},
    "capex": {2021: 1_200_000, 2022: 1_920_000, 2023: 2_880_000, 2024: 3_225_600},
    "depreciation": {2021: 600_000, 2022: 960_000, 2023: 1_440_000, 2024: 1_612_800},
    "nwc": {2021: 1_800_000, 2022: 2_880_000, 2023: 4_320_000, 2024: 6_048_000},
    "tax_rate": 0.25,
    "shares_outstanding": 50_000_000,
    "net_debt": -15_000_000,  # negative = net cash
}
```

Base case assumptions:

```python
assumptions = {
    "revenue_growth_rates": [0.35, 0.30, 0.25, 0.20, 0.15],  # FY2025-FY2029 declining growth
    "gross_margin": 0.74,  # target gross margin
    "opex_as_pct_revenue": [0.55, 0.50, 0.45, 0.42, 0.40],  # improving leverage
    "capex_as_pct_revenue": 0.08,
    "nwc_as_pct_revenue": 0.15,
    "tax_rate": 0.25,
    "risk_free_rate": 0.043,  # 10-year Treasury
    "equity_risk_premium": 0.055,
    "beta": 1.35,
    "cost_of_debt": 0.065,
    "debt_to_total_capital": 0.15,
    "terminal_growth_rate": 0.03,
    "exit_ev_ebitda_multiple": 20.0,
}
```

### DCF Model (`models/dcf_model.py`)

Class `DCFModel`:

- `__init__(self, historical: dict, assumptions: dict)`.
- `project_financials(self) -> pd.DataFrame`: Project revenue, COGS, gross profit, OpEx, EBITDA, EBIT, taxes, NOPAT, D&A, CapEx, change in NWC, unlevered free cash flow (UFCF) for FY2025-FY2029.
- `calculate_wacc(self) -> float`: WACC = (E/V) × Re + (D/V) × Rd × (1 - tax). Re = risk-free + beta × ERP. Return WACC as decimal.
- `terminal_value_perpetuity(self, final_fcf: float, wacc: float) -> float`: TV = FCF × (1 + g) / (WACC - g).
- `terminal_value_exit_multiple(self, final_ebitda: float) -> float`: TV = EBITDA × multiple.
- `discount_cash_flows(self, cash_flows: list[float], wacc: float) -> float`: Sum of FCF_t / (1 + WACC)^t.
- `enterprise_value(self, method: str = "perpetuity") -> float`: PV of FCFs + PV of terminal value.
- `equity_value(self, method: str = "perpetuity") -> float`: EV - net debt.
- `equity_value_per_share(self, method: str = "perpetuity") -> float`: Equity value / shares outstanding.
- `implied_multiples(self) -> dict`: Return implied EV/Revenue, EV/EBITDA, P/E for current year.

### Monte Carlo Simulation (`models/monte_carlo.py`)

Class `MonteCarloValuation`:

- `__init__(self, base_model: DCFModel, n_iterations: int = 5000, seed: int = 42)`.
- Distribution definitions:
  - `revenue_growth_y1`: `np.random.triangular(0.25, 0.35, 0.45)` (min, mode, max).
  - `revenue_growth_decay`: `np.random.normal(0.04, 0.01)` (how much growth declines each year).
  - `gross_margin`: `np.random.normal(0.74, 0.03)`.
  - `opex_efficiency_gain`: `np.random.uniform(0.02, 0.04)` (annual OpEx improvement).
  - `wacc`: `np.random.normal(assumptions_wacc, 0.01)`.
  - `terminal_growth`: `np.random.triangular(0.02, 0.03, 0.04)`.
- `run(self) -> pd.DataFrame`: Run all iterations, return DataFrame with columns: `iteration`, `ev`, `equity_value`, `per_share_value`, `implied_ev_revenue`.
- `statistics(self) -> dict`: Return mean, median, std, min, max, percentiles (5th, 25th, 50th, 75th, 95th).
- `confidence_interval(self, level: float = 0.90) -> tuple[float, float]`: Return (lower, upper) bounds.
- `probability_above(self, threshold: float) -> float`: Probability that equity value per share exceeds threshold.
- `value_at_risk(self, confidence: float = 0.95) -> float`: 5th percentile of per-share value distribution.

### Sensitivity Analysis (`models/sensitivity.py`)

Class `SensitivityAnalysis`:

- `two_way_table(self, var1_name: str, var1_range: list, var2_name: str, var2_range: list) -> pd.DataFrame`: Computes equity value per share for every combination.

Tables to generate:
1. **Revenue Growth (Y1) × WACC**: growth range [20%, 25%, 30%, 35%, 40%, 45%], WACC range [8%, 9%, 10%, 11%, 12%, 13%].
2. **Revenue Growth (Y1) × Exit Multiple**: growth range same, multiple range [15x, 18x, 20x, 22x, 25x, 30x].
3. **Terminal Growth × WACC**: terminal growth [1%, 2%, 3%, 4%, 5%], WACC same.

- `tornado_chart_data(self) -> list[dict]`: For each key variable, compute equity value at -20% and +20% of base assumption. Return sorted by impact (widest range first). Variables: revenue growth Y1, WACC, beta, exit multiple, terminal growth, gross margin, tax rate.

### Scenario Analysis (`models/scenario_analysis.py`)

Three scenarios:

| Parameter | Bear (25% weight) | Base (50% weight) | Bull (25% weight) |
|---|---|---|---|
| Revenue Growth Y1 | 20% | 35% | 45% |
| Growth Decay per Year | 6% | 4% | 2% |
| Target Gross Margin | 70% | 74% | 78% |
| Opex % of Revenue (FY2029) | 48% | 40% | 35% |
| Exit EV/EBITDA | 15x | 20x | 28x |
| Terminal Growth | 2% | 3% | 3.5% |

- `run_scenarios(self) -> dict`: Return per-scenario: EV, equity value, equity per share, implied multiples.
- `probability_weighted_value(self) -> float`: Sum(weight_i × equity_value_i).
- `scenario_comparison_table(self) -> pd.DataFrame`: Side-by-side comparison of all metrics.

### Unit Tests (`tests/test_dcf.py`)

- Test WACC calculation against hand-computed expected value (within 0.1% tolerance).
- Test terminal value perpetuity: FCF=$10M, WACC=10%, g=3% → TV = $10M × 1.03 / 0.07 = $147.14M.
- Test discount factor: $100M at year 3 with WACC 10% → $75.13M PV.
- Test equity value = enterprise value + net cash (negative net debt).
- Test Monte Carlo produces 5,000 results with mean within 15% of base case DCF.
- Test sensitivity table dimensions match input ranges.

### Expected Functionality

- `python -m models.dcf_model` → prints base case equity value per share using both terminal value methods.
- `python -m models.monte_carlo` → runs 5,000 iterations, prints statistics and 90% confidence interval.
- `python -m models.sensitivity` → prints 3 sensitivity tables and tornado chart ranking.
- `python -m models.scenario_analysis` → prints scenario comparison and probability-weighted value.
- `pytest tests/test_dcf.py` → all tests pass.

## Acceptance Criteria

- DCF model projects 5-year FCFs from historical data applying growth rates, margin assumptions, CapEx%, and NWC%.
- WACC computed from CAPM (risk-free + beta × ERP) and weighted with after-tax cost of debt.
- Terminal value computed by both perpetuity growth method and exit EV/EBITDA multiple method.
- Cash flows discounted to present value using `FCF_t / (1 + WACC)^t`.
- Equity value = Enterprise Value - Net Debt (adding back net cash position).
- Monte Carlo samples from triangular, normal, and uniform distributions for 5,000 iterations.
- Monte Carlo output includes mean, median, percentiles (5th through 95th), confidence interval, and probability above threshold.
- Sensitivity analysis generates two-way data tables for 3 variable pairs with grid of equity value per share.
- Tornado chart data ranks variables by impact magnitude on equity value.
- Scenario analysis defines bull/base/bear with probability weights summing to 100% and computes expected value.
- Unit tests validate WACC, terminal value, discount factor, and Monte Carlo output statistics.
