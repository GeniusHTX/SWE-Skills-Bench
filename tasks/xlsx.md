# Task: Implement Sales Report Generation Engine for openpyxl

## Background

We need to add a report generation engine to the openpyxl library that can produce Excel reports with automated summary formulas, conditional formatting, and trend charts.

## Files to Create/Modify

- `openpyxl/utils/report_engine.py` - Report generation engine (new)

## Requirements

### report_engine.py

Implement a `generate_sales_report(data: List[Dict], output_path: str) -> None` function that:

**Sheet1 - Raw Data with Summary:**
- Write input data (list of dicts with month, product, amount) to cells
- Insert `SUM` and `AVERAGE` formulas in a summary row at the bottom

**Sheet2 - Conditional Formatting:**
- Apply conditional formatting to the 'amount' column
- Red background (`PatternFill` with `fgColor=FF0000`) for month-over-month decline > 10%

**Sheet3 - Trend Chart:**
- `LineChart` showing monthly sales trend
- Proper axis labels and title

### Additional Examples (in the same module or separate helper):
- `BarChart` for category comparison
- `PieChart` for distribution
- Combined chart with secondary axis (optional)

## Expected Functionality

- Generated `.xlsx` files are valid (`load_workbook` succeeds)
- Summary formulas compute correctly
- Conditional formatting rules apply to correct cells
- charts render with correct data ranges

## Acceptance Criteria

- `openpyxl/utils/report_engine.py` compiles without syntax errors
- Generated Excel files are valid and contain all three sheets
- Formulas, conditional formatting, and charts are properly configured
