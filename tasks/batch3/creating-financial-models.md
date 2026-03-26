# Task: Build a DCF Valuation Engine with Sensitivity Analysis for QuantLib

## Background

QuantLib (https://github.com/lballabio/QuantLib) is a comprehensive library for quantitative finance. The project needs a discounted cash flow (DCF) valuation engine that can model multi-year free cash flow projections, apply terminal value calculations, and run sensitivity analysis across key assumptions. This component should integrate with QuantLib's existing date handling and interest rate framework.

## Files to Create/Modify

- `ql/models/dcf_valuation.hpp` (create) — C++ header for the DCF valuation engine class
- `ql/models/dcf_valuation.cpp` (create) — Implementation of DCF calculations, terminal value, and sensitivity grid
- `test-suite/dcfvaluation.cpp` (create) — Test cases for DCF valuation engine
- `test-suite/dcfvaluation.hpp` (create) — Test suite header

## Requirements

### Free Cash Flow Projection

- Accept a base-year free cash flow (FCF) amount in USD
- Project FCFs for a configurable number of years (default: 5) using a vector of annual growth rates
- Support two growth modes: constant growth (single rate applied to all years) and custom growth (per-year growth rate vector)
- If the custom growth vector is shorter than the projection period, repeat the last rate for remaining years
- All FCF values must be positive; raise an error if base FCF is zero or negative

### Terminal Value Calculation

- Support two terminal value methods:
  - **Gordon Growth Model**: TV = FCF_final × (1 + g) / (WACC − g), where g is the perpetuity growth rate
  - **Exit Multiple**: TV = FCF_final × multiple (configurable EV/FCF multiple)
- If the perpetuity growth rate >= WACC in the Gordon Growth Model, raise an error (result would be undefined or negative)
- Terminal value is discounted back to present along with projected FCFs

### Discount Rate and Present Value

- Accept a weighted average cost of capital (WACC) as the discount rate
- Discount each projected FCF and the terminal value to present using: PV = CF / (1 + WACC)^t
- The enterprise value is the sum of all discounted FCFs plus the discounted terminal value
- Support an optional net debt adjustment to derive equity value: Equity Value = Enterprise Value − Net Debt

### Sensitivity Analysis

- Generate a 2D sensitivity grid varying two parameters:
  - Rows: WACC values (e.g., 8% to 12% in 0.5% increments)
  - Columns: perpetuity growth rates (e.g., 1% to 4% in 0.5% increments)
- Each cell contains the resulting enterprise value
- Skip cells where perpetuity growth rate >= WACC (mark as N/A)
- Return the grid as a matrix with labeled row and column headers

### Expected Functionality

- A DCF with base FCF = $100M, 5 years at 10% growth, WACC = 10%, Gordon terminal growth = 3% produces an enterprise value calculable analytically
- Changing WACC from 10% to 12% decreases the enterprise value
- Exit multiple method with multiple = 15x produces TV = 15 × final year FCF
- Sensitivity grid with WACC [8%, 9%, 10%] and growth [2%, 3%] produces a 3×2 matrix of enterprise values
- Setting perpetuity growth = WACC raises an error, not division by zero

## Acceptance Criteria

- FCF projection handles both constant and custom per-year growth rate modes correctly
- Gordon Growth Model and Exit Multiple terminal value methods produce correct results
- Present value discounting is mathematically correct with PV = CF / (1 + WACC)^t
- Perpetuity growth rate >= WACC is rejected with a descriptive error
- Sensitivity analysis generates a correctly dimensioned grid with labeled headers
- Cells where growth >= WACC are marked as N/A in the sensitivity grid
- Equity value calculation correctly subtracts net debt from enterprise value
- Tests verify calculations against hand-computed expected values with tolerance ≤ 0.01
