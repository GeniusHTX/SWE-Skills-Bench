# Task: Implement a DCF Valuation Instrument and Sensitivity Analyzer in QuantLib

## Background

QuantLib (https://github.com/lballabio/QuantLib) is a C++ library for quantitative finance. The library provides instruments, pricing engines, and term structure utilities, but lacks a dedicated Discounted Cash Flow (DCF) valuation instrument for corporate finance use cases. The task is to implement a `DcfValuation` instrument with a corresponding pricing engine that performs free cash flow discounting, terminal value calculation, and sensitivity analysis on discount rate and growth rate inputs.

## Files to Create/Modify

- `ql/instruments/dcfvaluation.hpp` (create) — Header for the `DcfValuation` instrument class
- `ql/instruments/dcfvaluation.cpp` (create) — Implementation of the `DcfValuation` instrument
- `ql/pricingengines/dcf/dcfengine.hpp` (create) — Header for the `DcfEngine` pricing engine
- `ql/pricingengines/dcf/dcfengine.cpp` (create) — Implementation of the DCF pricing engine with WACC discounting and terminal value
- `ql/pricingengines/dcf/sensitivityanalyzer.hpp` (create) — Header for sensitivity analysis utility
- `ql/pricingengines/dcf/sensitivityanalyzer.cpp` (create) — Sensitivity analysis implementation (two-variable data table)
- `test-suite/dcfvaluation.cpp` (create) — Unit tests for the instrument, engine, and sensitivity analyzer
- `test-suite/dcfvaluation.hpp` (create) — Test suite header
- `ql/CMakeLists.txt` (modify) — Add new source files to the build
- `test-suite/CMakeLists.txt` (modify) — Add test suite to the build

## Requirements

### `DcfValuation` Instrument (`dcfvaluation.hpp/cpp`)

Inherits from `QuantLib::Instrument`. Represents a company valuation based on projected free cash flows.

#### Constructor
```cpp
DcfValuation(
    std::vector<Real> projectedFCF,        // Free cash flows for each projection year
    Rate terminalGrowthRate,               // Long-term growth rate for terminal value (e.g., 0.025 for 2.5%)
    Rate wacc,                             // Weighted average cost of capital (e.g., 0.10 for 10%)
    Real netDebt,                          // Net debt to subtract from enterprise value
    Real sharesOutstanding                 // Number of shares for per-share valuation
);
```

#### Results (accessible after `performCalculations`)
- `enterpriseValue()` — Returns total enterprise value (PV of projected FCFs + PV of terminal value)
- `equityValue()` — Returns `enterpriseValue() - netDebt`
- `valuePerShare()` — Returns `equityValue() / sharesOutstanding`
- `terminalValue()` — Returns the undiscounted terminal value: `lastFCF * (1 + terminalGrowthRate) / (wacc - terminalGrowthRate)`
- `pvOfTerminalValue()` — Returns the present value of terminal value discounted at WACC
- `pvOfProjectedFCF()` — Returns the sum of present values of projected free cash flows

#### Validation
- `wacc` must be greater than `terminalGrowthRate` (otherwise throw `Error("WACC must exceed terminal growth rate")`)
- `projectedFCF` must not be empty
- `sharesOutstanding` must be positive
- `wacc` and `terminalGrowthRate` must be non-negative

### `DcfEngine` Pricing Engine (`dcfengine.hpp/cpp`)

Inherits from `QuantLib::GenericEngine<DcfValuation::arguments, DcfValuation::results>`.

#### Calculation Logic
1. Discount each projected FCF at the WACC: $PV_i = \frac{FCF_i}{(1 + WACC)^i}$ for $i = 1, 2, \ldots, n$
2. Compute terminal value: $TV = \frac{FCF_n \times (1 + g)}{WACC - g}$ where $g$ is the terminal growth rate
3. Discount terminal value: $PV_{TV} = \frac{TV}{(1 + WACC)^n}$
4. Enterprise value: $EV = \sum_{i=1}^{n} PV_i + PV_{TV}$
5. Store all intermediate results in the `results` structure

### `SensitivityAnalyzer` (`sensitivityanalyzer.hpp/cpp`)

Utility class that generates a two-dimensional data table showing how the valuation changes across ranges of two input variables.

#### Constructor
```cpp
SensitivityAnalyzer(
    const DcfValuation& instrument,
    std::vector<Rate> waccRange,           // Row variable: range of WACC values to test
    std::vector<Rate> growthRateRange      // Column variable: range of terminal growth rates to test
);
```

#### Methods
- `computeTable() -> Matrix` — Returns a `QuantLib::Matrix` where entry `(i, j)` is the equity value per share computed with `waccRange[i]` and `growthRateRange[j]`, holding all other inputs constant
- `maxValue() -> Real` — Returns the maximum value in the computed table
- `minValue() -> Real` — Returns the minimum value in the computed table
- `baseCase() -> Real` — Returns the value per share using the instrument's original WACC and terminal growth rate

#### Validation
- Every combination of `waccRange[i]` and `growthRateRange[j]` must satisfy `wacc > growth rate`; entries that violate this are set to `Null<Real>()`

### Build Integration

- Add `ql/instruments/dcfvaluation.cpp` and `ql/pricingengines/dcf/dcfengine.cpp` and `ql/pricingengines/dcf/sensitivityanalyzer.cpp` to the `ql/CMakeLists.txt` source list
- Add `test-suite/dcfvaluation.cpp` to the `test-suite/CMakeLists.txt` source list and register the test suite

## Expected Functionality

- Given projected FCFs of `[100, 110, 121, 133.1, 146.41]` million, terminal growth rate 2.5%, WACC 10%, net debt $200M, 50M shares:
  - Terminal value = $146.41M × 1.025 / (0.10 − 0.025) = $2,002.6M$ (approximately)
  - PV of terminal value ≈ $1,243.5M$ (discounted 5 years at 10%)
  - PV of projected FCFs ≈ $460.8M$
  - Enterprise value ≈ $1,704.3M$
  - Equity value ≈ $1,504.3M$
  - Value per share ≈ $30.09

- A sensitivity table with WACC range `[0.08, 0.09, 0.10, 0.11, 0.12]` and growth range `[0.02, 0.025, 0.03]` produces a 5×3 matrix of per-share values, with higher values at lower WACC / higher growth rate

## Acceptance Criteria

- `DcfValuation` construct validates inputs and throws on invalid parameters
- `DcfEngine::calculate()` computes enterprise value, equity value, value per share, terminal value, PV of terminal value, and PV of projected FCFs
- Computed values match hand-calculated expected values within a tolerance of 0.01
- `SensitivityAnalyzer::computeTable()` produces a correctly sized matrix with valid entries for all feasible WACC/growth combinations
- Invalid combinations (WACC ≤ growth rate) produce `Null<Real>()` entries instead of throwing
- The project builds without errors after adding new files to `CMakeLists.txt`
- All test cases in `test-suite/dcfvaluation.cpp` pass
