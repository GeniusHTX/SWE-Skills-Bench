# Task: Implement a DCF Valuation Engine in QuantLib

## Background

QuantLib (https://github.com/lballabio/QuantLib) is a comprehensive library for quantitative finance. A new asset valuation class is needed that implements discounted cash flow (DCF) analysis, allowing users to compute the present value of projected cash flows under configurable discount rate assumptions.

## Files to Create/Modify

- `ql/instruments/dcfvaluation.hpp` (create) — DCF valuation class header with interface declarations
- `ql/instruments/dcfvaluation.cpp` (create) — DCF valuation class implementation
- `ql/CMakeLists.txt` (modify) — Add new source files to the build

## Requirements

### DCF Engine

- Implement a class that accepts a series of projected cash flows with their timing and computes the net present value using a discount rate or yield curve
- Support both flat discount rates and term-structure-based discounting
- Allow sensitivity analysis by computing NPV across a range of discount rates

### Cash Flow Modeling

- Support irregular cash flow timing (not just fixed intervals)
- Handle terminal value estimation for perpetuity-based DCF models
- Validate inputs: reject negative discount rates, empty cash flow series, and cash flows with dates in the past relative to the valuation date

### Integration

- Follow QuantLib's naming conventions, header organization, and build system integration
- The new files must compile as part of the existing CMake build

## Expected Functionality

- Computing NPV for a set of cash flows at a given discount rate returns the correct present value
- Sensitivity analysis produces a series of NPV values across discount rate scenarios
- Invalid inputs produce clear error messages

## Acceptance Criteria

- The new DCF valuation class can compute net present value from a schedule of projected cash flows and a discount assumption.
- Both flat-rate discounting and term-structure-based discounting are supported through the class interface.
- Sensitivity analysis can produce NPV results across multiple discount-rate scenarios.
- Invalid inputs such as empty cash-flow series, negative discount rates, or past-dated cash flows are rejected with clear errors.
- The implementation fits QuantLib's instrument and engine conventions rather than behaving as a standalone ad hoc utility.
