# Task: Create a Financial Report Generator with Charts and Formulas in openpyxl

## Background

The openpyxl library (https://github.com/ericgazoni/openpyxl) is a Python library for reading and writing Excel files. The task is to build a financial report generator module that creates a multi-sheet Excel workbook containing an income statement, a balance sheet, and a dashboard sheet with charts — all using openpyxl's formula engine, number formatting, conditional formatting, and chart capabilities.

## Files to Create/Modify

- `openpyxl/report/__init__.py` (create) — Package init exporting the `FinancialReportGenerator` class
- `openpyxl/report/generator.py` (create) — Core generator class that builds the multi-sheet workbook with formulas, formatting, and charts
- `openpyxl/report/styles.py` (create) — Reusable cell style definitions (currency format, percentage format, header style, alternating row colors, conditional formatting rules)
- `openpyxl/report/charts.py` (create) — Chart builder functions for bar charts, line charts, and pie charts used in the dashboard sheet
- `tests/test_report_generator.py` (create) — Tests verifying workbook structure, formula correctness, formatting, and chart presence

## Requirements

### Workbook Structure

- The generator must produce a workbook with exactly three sheets named `"Income Statement"`, `"Balance Sheet"`, and `"Dashboard"`
- The generator accepts a Python dictionary of financial data as input (revenues, expenses, assets, liabilities, equity) for a configurable number of periods (months or quarters)

### Income Statement Sheet

- Row categories: `Revenue`, `Cost of Goods Sold`, `Gross Profit`, `Operating Expenses` (broken into `Salaries`, `Rent`, `Marketing`, `Other`), `Operating Income`, `Interest Expense`, `Net Income`
- Columns: one per period (e.g., Q1 through Q4) plus a `Total` column
- `Gross Profit` must be a formula: `=Revenue - COGS` (cell references, not hardcoded values)
- `Operating Income` must be a formula: `=Gross Profit - sum of operating expense rows`
- `Net Income` must be a formula: `=Operating Income - Interest Expense`
- The `Total` column must use `SUM` formulas across all period columns for each row
- Currency cells must use the accounting number format `#,##0.00` with a dollar sign
- Negative values must display in red using conditional formatting

### Balance Sheet Sheet

- Row categories: **Assets** (`Cash`, `Accounts Receivable`, `Inventory`, `Fixed Assets`, `Total Assets`), **Liabilities** (`Accounts Payable`, `Short-term Debt`, `Long-term Debt`, `Total Liabilities`), **Equity** (`Common Stock`, `Retained Earnings`, `Total Equity`), `Total Liabilities & Equity`
- `Total Assets` must be a `SUM` formula of asset rows
- `Total Liabilities` must be a `SUM` formula of liability rows
- `Total Equity` must be a `SUM` formula of equity rows
- `Total Liabilities & Equity` must be a formula: `=Total Liabilities + Total Equity`
- A validation check row must compute `Total Assets - Total Liabilities & Equity` and apply conditional formatting: green if zero, red if non-zero

### Dashboard Sheet

- A bar chart comparing Revenue vs. Net Income across all periods
- A line chart showing Revenue trend across periods
- A pie chart showing the breakdown of Operating Expenses (Salaries, Rent, Marketing, Other) for the total column
- Each chart must have a title, axis labels, and a legend
- Charts must reference data in the Income Statement sheet via cross-sheet cell references

### Formatting

- Header rows must have bold white text on a dark blue background
- Data rows must alternate between white and light gray fill
- All currency values must use accounting format with two decimal places
- Percentage values (e.g., gross margin, operating margin) must use `0.0%` format
- Column widths must be auto-adjusted to fit content (minimum 12 characters)

### API

- `FinancialReportGenerator(data: dict)` constructor accepts the financial data dictionary
- `generate(filepath: str)` method writes the workbook to the specified path
- `generate_bytes() -> bytes` method returns the workbook as bytes for streaming
- The data dictionary schema must be validated; missing required keys raise `ValueError` with a descriptive message

## Expected Functionality

- Calling `FinancialReportGenerator(data).generate("report.xlsx")` produces a valid `.xlsx` file with three sheets
- Opening the workbook in Excel shows formulas that compute correctly (Gross Profit = Revenue − COGS, etc.)
- The Dashboard sheet displays three charts with correct data ranges
- Negative Net Income cells appear in red
- The Balance Sheet validation row shows green (0) when assets equal liabilities + equity
- Passing an incomplete data dictionary raises `ValueError`

## Acceptance Criteria

- The generated workbook contains exactly three sheets: "Income Statement", "Balance Sheet", "Dashboard"
- All computed rows (Gross Profit, Operating Income, Net Income, Total Assets, Total Liabilities, Total Equity) use Excel formulas referencing other cells, not hardcoded values
- The Dashboard sheet contains at least three chart objects (bar, line, pie) with proper titles and legends
- Currency formatting displays values as `$#,##0.00` and negative values appear in red via conditional formatting
- The Balance Sheet validation row applies green/red conditional formatting based on the balance check
- Invalid input data raises `ValueError` with a message identifying the missing fields
- Tests verify sheet names, formula cell types, chart counts, conditional formatting rules, and error handling
