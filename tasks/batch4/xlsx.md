# Task: Create Multi-Sheet Financial Summary Workbook from Raw Data

## Background

The openpyxl repository (https://github.com/ericgazoni/openpyxl) is a Python library for reading and writing Excel files. A new script is needed to generate a multi-sheet financial summary workbook that demonstrates advanced Excel features: cross-sheet formula references, conditional formatting, named ranges, data validation, charts, and professional formatting — all using openpyxl and Excel-native formulas rather than hardcoded Python calculations.

## Files to Create/Modify

- `examples/financial_summary.py` (create) — Script that generates the complete multi-sheet financial workbook
- `examples/financial_summary_output.xlsx` (create) — The generated output workbook (produced by running the script)

## Requirements

### Workbook Structure

The generated workbook must contain four sheets:

**Sheet 1: "Assumptions"**
- Contains all input assumptions in labeled rows: revenue growth rates (Years 1–5), COGS margin, operating expense ratio, tax rate, discount rate, and terminal growth rate
- Input cells must have yellow background fill and blue font to indicate they are user-editable
- All assumption cells must be defined as named ranges (e.g., `rev_growth_y1`, `cogs_margin`, `tax_rate`)

**Sheet 2: "Income Statement"**
- Columns: Year labels (Year 0 through Year 5) plus row labels
- Rows: Revenue, COGS, Gross Profit, Operating Expenses, EBIT, Taxes, Net Income
- Year 0 Revenue is a hardcoded base value ($10,000,000); subsequent years use formulas referencing revenue growth assumptions from the Assumptions sheet
- COGS, Operating Expenses, Taxes must all be formulas referencing the corresponding assumption cells — no hardcoded percentages
- Gross Profit = Revenue - COGS (formula); EBIT = Gross Profit - Operating Expenses (formula); Net Income = EBIT - Taxes (formula)
- Negative values must display in red font with parentheses

**Sheet 3: "DCF Valuation"**
- Rows: Free Cash Flow (linked from Net Income with an adjustment factor), Discount Factor, Present Value, Cumulative PV, Terminal Value, Enterprise Value
- Free Cash Flow formulas must reference Net Income from the Income Statement sheet
- Discount factor formula: `1 / (1 + discount_rate) ^ year`
- Present Value = FCF × Discount Factor (formula)
- Terminal Value = final year FCF × (1 + terminal_growth) / (discount_rate - terminal_growth) (formula)
- Enterprise Value = sum of all Present Values + discounted Terminal Value (formula)

**Sheet 4: "Dashboard"**
- A bar chart showing Revenue and Net Income side by side for Years 1–5
- A summary table pulling Enterprise Value, final year Revenue, and final year Net Income from the other sheets using cross-sheet formulas
- Data validation dropdown for a "Scenario" cell with options: "Base", "Optimistic", "Pessimistic" (the dropdown must be functional in Excel)

### Formatting Requirements

- All sheets must use Arial font (size 11 for body, size 14 bold for sheet titles)
- Currency values must use the `$#,##0` number format with negative values in parentheses
- Percentages must use `0.0%` format
- Column widths must be set so that all content is visible without truncation
- Header rows must have a dark blue background with white bold text
- Alternating row shading (light gray / white) for data rows on Income Statement and DCF sheets

### Formula Integrity

- The workbook must contain zero formula errors (`#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, `#NAME?`)
- All calculations must use Excel formulas and cell references — no values computed in Python and written as constants
- Changing an assumption value in the Assumptions sheet must propagate through all dependent cells when the workbook is opened in Excel

### Expected Functionality

- Running `python examples/financial_summary.py` produces `examples/financial_summary_output.xlsx` without errors
- Opening the output in Excel shows four properly named and formatted sheets
- Changing the Year 1 revenue growth rate on the Assumptions sheet from the default to 15% causes Year 1 Revenue on the Income Statement to update automatically
- The bar chart on the Dashboard sheet displays Revenue and Net Income bars for five projection years
- The scenario dropdown on the Dashboard sheet offers three choices and can be selected in Excel
- Enterprise Value on the DCF sheet updates when the discount rate assumption is changed

## Acceptance Criteria

- The script runs without errors and produces a valid `.xlsx` file
- The workbook contains exactly four sheets: "Assumptions", "Income Statement", "DCF Valuation", "Dashboard"
- All monetary values on Income Statement and DCF sheets are computed via Excel formulas referencing Assumptions, not hardcoded
- Cross-sheet references (Income Statement → Assumptions, DCF → Income Statement, Dashboard → DCF) work correctly
- The workbook opens in Excel/LibreOffice with zero formula errors
- Formatting follows the specified color coding, number formats, and font rules
- The Dashboard contains a functional bar chart and a working data validation dropdown
