# Task: Implement a Financial Report Generator with openpyxl

## Background

openpyxl (https://github.com/ericgazoni/openpyxl) is a Python library for reading and writing Excel files. A comprehensive example is needed that demonstrates advanced spreadsheet automation: building a multi-sheet financial report workbook with formatted tables, formulas, conditional formatting, data validation, and charts. The report must model a company's quarterly income statement, balance sheet, and a sensitivity analysis dashboard.

## Files to Create/Modify

- `openpyxl/sample/financial_report.py` (create) — Main script generating a complete 4-sheet Excel workbook: Assumptions, Income Statement, Balance Sheet, and Dashboard
- `openpyxl/sample/formatting.py` (create) — Shared formatting utilities: number formats, color coding (blue for inputs, black for formulas, green for links, red for external references), border styles, and header formatting
- `openpyxl/sample/formulas.py` (create) — Formula builder functions that construct Excel formula strings for revenue projections, expense calculations, and ratio computations
- `openpyxl/sample/charts.py` (create) — Chart creation functions: revenue bar chart, margin line chart, and sensitivity tornado chart
- `tests/test_financial_report.py` (create) — Tests validating workbook structure, formula correctness, formatting, and data validation rules

## Requirements

### Workbook Structure

- **Sheet 1: "Assumptions"** — Input cells for base revenue ($10M), revenue growth rate (8%), COGS percentage (60%), SG&A percentage (15%), tax rate (21%), capex percentage (5%), and depreciation rate (10%); all input cells colored blue with data validation ranges
- **Sheet 2: "Income Statement"** — Quarterly income statement for 4 quarters with rows: Revenue, COGS, Gross Profit, SG&A, EBITDA, Depreciation, EBIT, Tax, Net Income; all values computed via Excel formulas referencing the Assumptions sheet
- **Sheet 3: "Balance Sheet"** — Simplified balance sheet with rows: Cash, Accounts Receivable (15% of revenue), Inventory (20% of COGS), Total Current Assets, PP&E (capex less depreciation), Total Assets, Accounts Payable (10% of COGS), Total Liabilities, Equity (Total Assets - Total Liabilities); formulas reference Income Statement values
- **Sheet 4: "Dashboard"** — Summary ratios (gross margin %, operating margin %, net margin %, return on equity) calculated via formulas, a revenue bar chart, a margin trend line chart, and a sensitivity table varying revenue growth (5%-11%) and COGS % (55%-65%)

### Formula Requirements

- All computed cells must use Excel formulas (e.g., `=Assumptions!B2*1.08`), not hardcoded Python-computed values
- Revenue for Q1 = base revenue from Assumptions; Q2-Q4 apply the growth rate compounding quarterly: `Q_n = Q_{n-1} * (1 + growth_rate/4)`
- COGS = Revenue × COGS percentage
- Gross Profit = Revenue - COGS
- SG&A = Revenue × SG&A percentage
- EBITDA = Gross Profit - SG&A
- EBIT = EBITDA - Depreciation
- Tax = max(EBIT × tax_rate, 0) — no negative tax
- Net Income = EBIT - Tax
- The workbook must contain zero circular references and zero formula errors (#REF!, #VALUE!, #DIV/0!)

### Formatting and Color Coding

- Input cells (Assumptions sheet): blue font (RGB `#0000FF`), light blue fill, unlocked for editing
- Formula cells: black font, no fill
- Cross-sheet reference cells (e.g., Dashboard referencing Income Statement): green font (RGB `#008000`)
- Negative values: red font (RGB `#FF0000`)
- Currency format: `#,##0` for whole numbers, `#,##0.00` for per-share values
- Percentage format: `0.0%`
- Header rows: bold, dark background fill, white font
- Column widths must be set to accommodate the longest value in each column

### Data Validation

- Revenue growth rate: decimal between 0% and 30%
- COGS percentage: decimal between 40% and 80%
- SG&A percentage: decimal between 5% and 30%
- Tax rate: decimal between 0% and 40%
- Invalid entries must show a validation error prompt with a descriptive message (e.g., "Growth rate must be between 0% and 30%")

### Charts

- Revenue bar chart on Dashboard: 4 bars (Q1-Q4), y-axis labeled "Revenue ($)", chart title "Quarterly Revenue"
- Margin line chart on Dashboard: 3 lines (gross margin %, operating margin %, net margin %) across Q1-Q4, with legend
- Both charts must reference Income Statement data cells (not hardcoded values)
- Chart dimensions: 15 columns wide, 10 rows tall

### Sensitivity Table

- Located on Dashboard sheet starting at row 20
- Rows vary revenue growth rate: 5%, 6%, 7%, 8%, 9%, 10%, 11%
- Columns vary COGS percentage: 55%, 58%, 60%, 62%, 65%
- Each cell contains the resulting annual net income calculated by formula or lookup
- The cell corresponding to the base case (8% growth, 60% COGS) must be highlighted with a yellow border

## Expected Functionality

- Running `python financial_report.py` generates `financial_report.xlsx` with 4 sheets
- Opening the workbook in Excel shows properly formatted tables with blue input cells, black formula cells, and green cross-references
- Changing the revenue growth rate in the Assumptions sheet automatically recalculates all Income Statement and Dashboard values
- Charts update dynamically when underlying data changes
- Data validation prevents entering invalid values (e.g., growth rate > 30%)
- The sensitivity table shows net income varying across 35 growth/COGS combinations

## Acceptance Criteria

- The generated workbook contains 4 sheets: Assumptions, Income Statement, Balance Sheet, and Dashboard
- All computed cells use Excel formulas referencing other cells, not Python-computed static values
- Opening the workbook produces zero formula errors (#REF!, #VALUE!, #DIV/0!, #NAME?)
- Input cells are color-coded blue; formula cells are black; cross-sheet references are green; negative values are red
- Data validation rules prevent out-of-range entries on the Assumptions sheet
- Revenue and margin charts are present on the Dashboard sheet with correct data references
- The sensitivity table contains 35 cells (7 growth rates × 5 COGS percentages) with the base case highlighted
- All tests pass with `pytest`
