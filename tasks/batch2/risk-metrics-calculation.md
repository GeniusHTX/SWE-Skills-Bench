# Task: Add a Risk Metrics Calculation Demo to pyfolio

## Background

Pyfolio (https://github.com/quantopian/pyfolio) is a portfolio and risk analytics library. A new example script is needed that demonstrates computing key risk metrics — VaR, CVaR, Sharpe ratio, Sortino ratio, and maximum drawdown — from a portfolio returns series.

## Files to Create

- `examples/risk_metrics_demo.py` — Risk metrics calculation demo script

## Requirements

### Risk Metrics

- Compute **Value at Risk (VaR)** at configurable confidence levels (e.g., 95%, 99%)
- Compute **Conditional VaR (CVaR / Expected Shortfall)** at the same confidence levels
- Compute **Sharpe ratio** given a risk-free rate parameter
- Compute **Sortino ratio** using downside deviation
- Compute **maximum drawdown** and its duration from a cumulative returns series

### Input Handling

- Accept a returns series (e.g., daily returns as a pandas Series or list of floats)
- Support configurable parameters: confidence level, risk-free rate, and analysis window
- Validate inputs: reject empty series, non-numeric values, or invalid confidence levels

### Output

- Print a formatted summary table of all computed metrics
- The script must have a `__main__` entry point for direct execution
- Must be syntactically valid and importable Python

## Expected Functionality

- Given a sample returns series, all five risk metrics are computed and printed
- Different confidence levels produce appropriately different VaR and CVaR values
- Edge cases (constant returns, single-period series) are handled gracefully

## Acceptance Criteria

- The script computes VaR, CVaR, Sharpe ratio, Sortino ratio, and maximum drawdown from a provided returns series.
- Confidence-level and risk-free-rate settings change the reported metrics in the expected direction.
- Invalid inputs such as empty data, non-numeric values, or invalid confidence levels are rejected clearly.
- Edge cases such as flat returns or short return series are handled without crashing.
- Output is presented in a readable summary that a user can inspect without reading the implementation.
