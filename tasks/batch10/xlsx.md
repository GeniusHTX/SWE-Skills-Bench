# Task: Create a Multi-Sheet Financial Comparison Workbook

## Background

The openpyxl library (https://github.com/ericgazoni/openpyxl) is used to build a financial comparison workbook that models quarterly revenue for three business divisions over two fiscal years (FY2025 and FY2026). The workbook must use Excel formulas for all computed values so the spreadsheet remains dynamic and recalculates when inputs change. No calculated value may be hardcoded from Python.

## Files to Create/Modify

- `scripts/build_financial_report.py` (new) — Python script that generates the workbook using openpyxl with formulas and formatting
- `output/financial_comparison.xlsx` (new) — The generated workbook, produced by running the script
- `tests/test_financial_report.py` (new) — Unit tests that load the generated workbook and verify formula presence, structure, and formatting

## Requirements

### Workbook Structure

- Sheet 1: **Assumptions** — Contains all input values (quarterly revenue figures, growth rates, tax rate, discount rate)
- Sheet 2: **Division Summary** — Quarterly revenue by division with cross-sheet references to Assumptions, computed totals, and year-over-year growth rates
- Sheet 3: **Consolidated P&L** — Aggregated revenue, COGS (as a percentage of revenue from Assumptions), gross profit, operating expenses, EBIT, taxes, and net income — all as Excel formulas
- Sheet 4: **Dashboard** — Key metrics (total revenue, average quarterly growth, highest/lowest performing division-quarter) computed via formulas referencing other sheets

### Assumptions Sheet (Sheet 1)

- Cell `B2`: Label "FY2025 Q1 Growth Rate", Cell `C2`: value `0.05` (formatted as percentage)
- Rows 2–9: Growth rates for FY2025 Q1–Q4 and FY2026 Q1–Q4
- Cell `B11`: "COGS % of Revenue", Cell `C11`: value `0.35`
- Cell `B12`: "Tax Rate", Cell `C12`: value `0.21`
- Cell `B13`: "OpEx (Fixed, $mm)", Cell `C13`: value `12.5`
- Input cells must use blue font (RGB 0,0,255)

### Division Summary Sheet (Sheet 2)

- Three divisions: "Cloud Services", "Enterprise Software", "Professional Services"
- Base revenue (FY2025 Q1) per division in row 3: `$45.0mm`, `$32.0mm`, `$18.0mm`
- Subsequent quarters computed as `=PreviousQuarter*(1+Assumptions!$C$N)` referencing the appropriate growth rate cell — NOT as Python-calculated values
- Row for each division showing 8 quarterly columns (FY2025 Q1–Q4, FY2026 Q1–Q4)
- A "Total" row using `=SUM()` formulas across divisions for each quarter
- A "YoY Growth" row computing `=(CurrentQ - PriorYearQ)/PriorYearQ` for FY2026 quarters
- Formula cells must use black font; cross-sheet references must use green font (RGB 0,128,0)

### Consolidated P&L Sheet (Sheet 3)

- Revenue row: `=` references to the Total row in Division Summary for each quarter
- COGS row: `=Revenue*Assumptions!$C$11` for each quarter
- Gross Profit: `=Revenue-COGS`
- Operating Expenses: `=Assumptions!$C$13` (fixed per quarter)
- EBIT: `=GrossProfit-OpEx`
- Taxes: `=MAX(EBIT*Assumptions!$C$12, 0)` (no tax on negative EBIT)
- Net Income: `=EBIT-Taxes`
- All values formatted as `$#,##0.0` with negative values in parentheses

### Dashboard Sheet (Sheet 4)

- "Total FY2025 Revenue": `=SUM(...)` referencing Q1–Q4 totals from Division Summary
- "Total FY2026 Revenue": same for FY2026 quarters
- "Full-Period Revenue Growth": `=(FY2026Total-FY2025Total)/FY2025Total` formatted as percentage
- "Highest Quarter": `=MAX(...)` across all 8 quarterly totals
- "Lowest Quarter": `=MIN(...)` across all 8 quarterly totals
- "Average Quarterly Net Income": `=AVERAGE(...)` referencing P&L Net Income row

### Formatting

- Header rows: bold, dark blue background (RGB 0,51,102) with white font
- All column widths auto-sized or set to at least 15 characters
- Font: Arial 10pt throughout
- Years formatted as text strings ("FY2025 Q1"), not as numbers
- Percentage cells formatted as `0.0%`

### Edge Cases

- `Taxes` formula must handle negative EBIT (operating loss) by using `MAX(..., 0)` — no negative tax
- Division by zero in YoY Growth must be guarded with `=IF(PriorQ=0, "", (CurrentQ-PriorQ)/PriorQ)`
- All formulas must be string formulas in openpyxl (e.g., `cell.value = '=SUM(B3:B5)'`), never Python-computed numeric assignments for derived values

## Acceptance Criteria

- Running `python scripts/build_financial_report.py` produces `output/financial_comparison.xlsx` without errors
- The workbook contains exactly 4 sheets named "Assumptions", "Division Summary", "Consolidated P&L", "Dashboard"
- Every computed cell in Division Summary, Consolidated P&L, and Dashboard contains an Excel formula string (starts with `=`), not a hardcoded numeric value
- Cross-sheet references correctly point to the Assumptions and Division Summary sheets
- Changing a growth rate in Assumptions and recalculating causes downstream values on all sheets to update accordingly
- Negative EBIT quarters produce zero tax, not negative tax
- YoY Growth cells for FY2026 do not produce `#DIV/0!` errors
- Color coding follows the specified convention: blue for inputs, black for formulas, green for cross-sheet references
- All tests in `tests/test_financial_report.py` pass, verifying formula presence, sheet structure, and formatting rules
