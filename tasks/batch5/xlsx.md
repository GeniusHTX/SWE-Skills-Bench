# Task: Create a Multi-Sheet Financial Report Workbook with Dynamic Formulas

## Background

openpyxl (https://github.com/ericgazoni/openpyxl) is the reference Python library for reading and writing Excel (`.xlsx`) files. This task requires building a script that generates a multi-sheet financial report workbook with dynamic formulas, conditional formatting, named ranges, and proper number formatting — a common requirement for financial reporting automation.

## Files to Create/Modify

- `openpyxl/sample/financial_report.py` (create) — Script that generates a complete financial report workbook (`financial_report.xlsx`) with three sheets: Income Statement, Balance Sheet, and Dashboard.
- `openpyxl/sample/tests/test_financial_report.py` (create) — Tests that verify the generated workbook structure, formula correctness, formatting, and recalculation results.

## Requirements

### Income Statement Sheet

- Columns: `A` = Line item label, `B–F` = Years 2021–2025.
- Row items: Revenue, Cost of Goods Sold, **Gross Profit** (formula: Revenue - COGS), Operating Expenses, **EBIT** (formula: Gross Profit - OpEx), Interest Expense, **EBT** (formula: EBIT - Interest), Tax (formula: EBT × 25%), **Net Income** (formula: EBT - Tax).
- Year-over-year growth row for Revenue: formula computing `(CurrentYear / PriorYear) - 1` for years 2022–2025.
- All monetary values formatted as `#,##0.00` with dollar sign; percentages formatted as `0.0%`.
- **Bold** font for all calculated subtotals (Gross Profit, EBIT, EBT, Net Income).
- Input cells (Revenue, COGS, OpEx, Interest) colored with a light blue background; formula cells left white.

### Balance Sheet Sheet

- Row items: Cash, Accounts Receivable, Inventory, **Total Current Assets** (formula: sum of above), Property & Equipment, **Total Assets** (formula: Current + PP&E), Accounts Payable, Short-Term Debt, **Total Current Liabilities** (sum), Long-Term Debt, **Total Liabilities** (sum), Shareholders' Equity, **Total L+E** (formula: Liabilities + Equity).
- Include a validation check row: `Total Assets - Total L+E` must equal 0 for each year.
- Conditional formatting: if the balance check ≠ 0, the cell turns red with white text.

### Dashboard Sheet

- A summary table pulling key metrics from the other sheets using cross-sheet references: Revenue, Net Income, Net Margin (Net Income / Revenue), Total Assets, and Debt-to-Equity ratio (Total Liabilities / Equity).
- A named range `NetIncomeRange` pointing to the Net Income row on the Income Statement.
- All cross-sheet references must use sheet-qualified formulas (e.g., `='Income Statement'!B10`).

### Data Population

- Populate input cells with sample data for 2021–2025: Revenue growing from $100M to $160M, COGS at 60% of revenue, OpEx at 20M growing 5%/year, Interest at $2M constant.
- Balance Sheet sample: Cash $15M, AR $20M, Inventory $10M, PP&E $50M, AP $8M, STD $5M, LTD $30M, Equity = Total Assets - Total Liabilities.

### Expected Functionality

- Opening the generated XLSX in Excel or LibreOffice → all formulas recalculate correctly; no `#REF!` or `#VALUE!` errors.
- The balance check row shows `$0.00` for all years; altering an input breaks the balance and turns the cell red.
- The Dashboard sheet shows correct cross-sheet values matching the Income Statement and Balance Sheet.
- Named range `NetIncomeRange` is navigable from the Name Box.

## Acceptance Criteria

- The generated workbook contains exactly three sheets: "Income Statement", "Balance Sheet", "Dashboard".
- All calculated rows use Excel formulas (not hardcoded values) that recalculate when inputs change.
- Number formatting applies correctly: currency with thousands separator for monetary values, percentage format for ratios.
- Conditional formatting on the balance check turns cells red when the value is non-zero.
- Cross-sheet references on the Dashboard resolve correctly.
- The named range `NetIncomeRange` is defined in the workbook.
- Tests verify: sheet count, formula presence in key cells, number format strings, conditional formatting rules, and named range existence.
- The workbook opens without errors in LibreOffice Calc and all formulas produce expected values.
