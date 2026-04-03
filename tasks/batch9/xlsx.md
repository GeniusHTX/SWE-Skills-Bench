# Task: Create a Multi-Sheet Financial Budget Model with Dynamic Formulas

## Background

Using the openpyxl library (https://github.com/ericgazoni/openpyxl), create a Python script that generates a professional multi-sheet Excel workbook for a three-year departmental budget. The workbook must use Excel formulas (not hardcoded Python-computed values), proper cell formatting with financial color coding conventions, and produce zero formula errors after recalculation.

## Files to Create/Modify

- `budget_model.py` (create) — Main script that generates the Excel workbook using openpyxl with all sheets, formulas, formatting, and data validation
- `output/department_budget.xlsx` (create) — The generated Excel workbook output

## Requirements

### Workbook Structure

- Sheet 1: **Assumptions** — Contains all input parameters: annual revenue growth rates (Year 1: 8%, Year 2: 12%, Year 3: 10%), department headcount, average salary per department, benefits rate (25%), office cost per employee ($2,400/year), software cost per employee ($1,200/year), and a contingency percentage (5%)
- Sheet 2: **Revenue** — Projects quarterly revenue for 3 years (12 quarters total). Base Q1 Year 1 revenue is $2,500,000. Each subsequent quarter applies the annual growth rate divided by 4. Annual totals must use `=SUM()` formulas over the four quarters. A grand total row must sum all 3 annual totals
- Sheet 3: **Expenses** — Calculates per-department expenses (Engineering, Sales, Marketing, Operations) for each year. Salary costs use `=headcount * avg_salary` referencing the Assumptions sheet. Benefits use `=salary_cost * benefits_rate`. Office and software costs each use `=headcount * per_employee_cost`. Department subtotals sum all cost categories. A `Total Expenses` row sums all departments. Contingency row uses `=Total_Expenses * contingency_pct`
- Sheet 4: **Summary** — Dashboard with: Total Revenue (linked from Revenue sheet), Total Expenses including contingency (linked from Expenses sheet), Net Income (`=Revenue - Expenses`), Net Margin (`=Net_Income / Revenue` formatted as percentage), Year-over-Year revenue growth for Years 2 and 3

### Formula Requirements

- Every calculated cell must use an Excel formula, not a Python-computed value
- Cross-sheet references must use the `SheetName!CellRef` syntax (e.g., `=Assumptions!B3`)
- No formula may produce `#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, or `#NAME?` errors after recalculation
- Division formulas must guard against zero denominators using `=IF(denominator=0, 0, numerator/denominator)` or equivalent

### Formatting Requirements

- Blue font (RGB: 0,0,255) for all hardcoded input values on the Assumptions sheet
- Black font (RGB: 0,0,0) for all formula cells
- Currency cells use `$#,##0` format with negative values in parentheses: `$#,##0;($#,##0);"-"`
- Percentage cells use `0.0%` format
- Header rows have bold font, gray background (RGB: 217,217,217), and bottom border
- Column widths are auto-sized or set to at least 15 characters for readability
- Year and quarter labels are formatted as text strings (e.g., "2026" not 2,026; "Q1" not a number)

### Data Validation

- The Assumptions sheet must include data validation on the growth rate cells restricting values to between -50% and 100%
- The contingency percentage cell must be restricted to between 0% and 20%

### Expected Functionality

- Opening `output/department_budget.xlsx` in Excel or LibreOffice shows correct formula results in all calculated cells
- Changing the Year 1 growth rate on the Assumptions sheet from 8% to 15% automatically recalculates all dependent Revenue and Summary cells
- The Summary sheet shows Net Margin as a percentage without manual recalculation
- All 4 department expense rows sum correctly to the Total Expenses row

## Acceptance Criteria

- The Python script `budget_model.py` runs without errors and produces `output/department_budget.xlsx`
- The workbook contains exactly 4 sheets named "Assumptions", "Revenue", "Expenses", and "Summary"
- Every calculated cell contains an Excel formula (not a hardcoded value); verifiable by opening with `data_only=False`
- After recalculation (via LibreOffice or `scripts/recalc.py`), no cells contain formula error values (`#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, `#NAME?`)
- Input cells on Assumptions use blue font; formula cells use black font
- Currency and percentage cells display in the specified number formats
- Cross-sheet references on Revenue, Expenses, and Summary correctly link to Assumptions values
