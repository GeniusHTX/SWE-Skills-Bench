# Task: Add Risk Metrics Calculation Examples and Tests

## Background

   Add example scripts and unit tests for risk metrics calculation in pyfolio,
   demonstrating Sharpe ratio, maximum drawdown, and other key metrics.

## Files to Create/Modify

- examples/risk_metrics_demo.py (new)
- tests/test_risk_metrics.py (new)
- notebooks/risk_metrics.ipynb (optional)

## Requirements

   Example Script:

- Small backtest example with sample price series
- Calculate key metrics:
  * Sharpe Ratio
  * Maximum Drawdown
  * Sortino Ratio
  * Calmar Ratio
- Output results to JSON/CSV

### Expected Functionality

- Test Sharpe calculation with known inputs
- Test Max Drawdown calculation
- Verify metrics within tolerance range

## Expected Functionality

- Sharpe ratio calculation matches expected formula
- Max drawdown correctly identifies peak-to-trough
- All metrics have proper handling of edge cases

## Acceptance Criteria

- Example script produces valid output
- Metrics calculated within acceptable tolerance
