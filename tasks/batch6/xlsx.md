# Task: Build a Financial Reporting Workbook from Raw Transaction Data

## Background

An accounting department needs an Excel workbook that consolidates raw transaction data into a professional financial report. The workbook has four sheets: raw data import, monthly summary with formulas, quarterly P&L statement, and a dashboard sheet with charts. All calculations must use Excel formulas (not hardcoded Python-computed values) so the spreadsheet remains dynamic when source data changes.

## Files to Create/Modify

- `scripts/build_financial_report.py` (create) — Python script using openpyxl to build the complete workbook with data, formulas, formatting, and charts
- `data/transactions.csv` (create) — Sample transaction dataset (200 rows) with columns: date, description, category, subcategory, amount, type (revenue/expense), department, payment_method
- `output/financial_report.xlsx` (create) — The generated Excel workbook (output of running the script)

## Requirements

### Transaction Data (`data/transactions.csv`)

Generate 200 rows of realistic transaction data spanning January 2024 through December 2024:
- Revenue categories: `Product Sales`, `Service Revenue`, `Subscription Revenue`, `Licensing Fees`.
- Expense categories: `Salaries`, `Office Rent`, `Software Licenses`, `Marketing`, `Travel`, `Utilities`, `Professional Services`, `Equipment`.
- Departments: `Engineering`, `Sales`, `Marketing`, `Operations`, `Finance`.
- Payment methods: `Wire Transfer`, `Credit Card`, `ACH`, `Check`.
- Amounts: Revenue transactions $1,000-$150,000. Expense transactions $500-$80,000.
- Ensure a mix ensuring total revenue > total expenses by roughly 15-20%.

### Sheet 1: Raw Data (`scripts/build_financial_report.py`)

- Sheet name: `"Transactions"`.
- Import all rows from `transactions.csv`.
- Column headers in row 1: `Date`, `Description`, `Category`, `Subcategory`, `Amount`, `Type`, `Department`, `Payment Method`.
- Format: header row bold with dark blue background (#1F4E79) and white text, alternating row colors (light gray #F2F2F2 / white), currency format `$#,##0.00` for Amount column, date format `YYYY-MM-DD`.
- Add Excel Table formatting (`Table1`) with auto-filter enabled.
- Freeze panes below header row.

### Sheet 2: Monthly Summary

- Sheet name: `"Monthly Summary"`.
- Structure:

| | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| 1 | **Month** | **Total Revenue** | **Total Expenses** | **Net Income** | **Margin %** | **Transaction Count** |
| 2 | Jan 2024 | `=SUMPRODUCT((MONTH(Transactions!A2:A201)=1)*(YEAR(Transactions!A2:A201)=2024)*(Transactions!F2:F201="revenue")*Transactions!E2:E201)` | (same pattern for expenses) | `=B2-C2` | `=IF(B2=0,"-",D2/B2)` | `=COUNTIFS(Transactions!A2:A201,">="&DATE(2024,1,1),Transactions!A2:A201,"<"&DATE(2024,2,1))` |
| ... | (rows 3-13 for Feb-Dec) | | | | | |
| 14 | **Total** | `=SUM(B2:B13)` | `=SUM(C2:C13)` | `=SUM(D2:D13)` | `=IF(B14=0,"-",D14/B14)` | `=SUM(F2:F13)` |

- Formatting: header row same blue style, totals row bold with top border, currency format for B-D columns, percentage format `0.0%` for Margin column, number format `#,##0` for count column.
- Conditional formatting: Margin % column — green background if ≥20%, yellow if 10-20%, red if <10%.

### Sheet 3: Quarterly P&L Statement

- Sheet name: `"P&L Statement"`.
- Layout mimicking a standard income statement:

```
                            Q1 2024     Q2 2024     Q3 2024     Q4 2024     FY 2024
Revenue
  Product Sales             =SUMPRODUCT(...)  ...    ...         ...         =SUM(B:E)
  Service Revenue           ...
  Subscription Revenue      ...
  Licensing Fees            ...
Total Revenue               =SUM(B4:B7)

Cost of Revenue
  (relevant expense items)
Gross Profit                =Total Revenue - Cost of Revenue

Operating Expenses
  Salaries                  =SUMPRODUCT(...)
  Office Rent               ...
  Marketing                 ...
  Software Licenses         ...
  Travel                    ...
  Utilities                 ...
  Professional Services     ...
  Equipment                 ...
Total Operating Expenses    =SUM(...)

Operating Income            =Gross Profit - Total OpEx
Operating Margin %          =Operating Income / Total Revenue
```

- All amounts must be Excel formulas referencing the `Transactions` sheet (SUMPRODUCT with month/year/category/type criteria).
- FY 2024 column: `=SUM` of Q1-Q4 columns (not re-querying raw data).
- Formatting:
  - Revenue items in blue text (RGB 0,0,255) as they reference source data.
  - Subtotals (Total Revenue, Gross Profit, Operating Income) bold with top+bottom borders.
  - Negative values in parentheses: `$#,##0;($#,##0);"-"`.
  - Percentages: `0.0%` format.
  - Column widths: A=35, B-F=15.
  - Section headers (Revenue, Operating Expenses) bold and indented category items.

### Sheet 4: Dashboard

- Sheet name: `"Dashboard"`.
- Charts (created via openpyxl):
  1. **Monthly Revenue vs Expenses** (BarChart): clustered bar chart, X-axis = months, two series (Revenue, Expenses) from Monthly Summary B2:C13. Title: "Monthly Revenue vs Expenses". Size: 15 columns × 20 rows.
  2. **Net Income Trend** (LineChart): line chart from Monthly Summary D2:D13. Title: "Net Income Trend". Include trend line.
  3. **Expense Breakdown by Category** (PieChart): pie chart showing total expenses per category using SUMPRODUCT formulas. Title: "Expense Distribution". Data labels showing percentage.
  4. **Revenue by Quarter** (BarChart): bar chart from P&L Statement Total Revenue row for Q1-Q4. Title: "Quarterly Revenue".

- Layout: charts positioned at A1, J1, A22, J22 (2×2 grid).
- Dashboard header: row 1 merged A1:S1 with title "Financial Dashboard — FY 2024", font size 16, bold, centered.

### Script Structure (`scripts/build_financial_report.py`)

The script must:
1. Read `data/transactions.csv` using `csv` module or `openpyxl`.
2. Create workbook with 4 sheets.
3. Populate Transactions sheet with data and formatting.
4. Build Monthly Summary with SUMPRODUCT/COUNTIFS formulas (not Python-computed values).
5. Build P&L Statement with SUMPRODUCT formulas referencing Transactions sheet.
6. Build Dashboard with 4 charts referencing summary data.
7. Save to `output/financial_report.xlsx`.
8. Print completion message with file path.

### Expected Functionality

- Open `output/financial_report.xlsx` in Excel → Transactions sheet shows formatted table with 200 rows of data.
- Monthly Summary auto-computes revenue, expenses, net income, margin for each month using Excel formulas.
- Changing an amount in the Transactions sheet → Monthly Summary and P&L recalculate automatically.
- P&L Statement shows standard income statement layout with quarterly and FY columns.
- Dashboard displays 4 charts showing revenue trends, expense breakdown, and quarterly comparisons.
- All formula cells display computed values after Excel recalculation (no #REF!, #DIV/0!, or #VALUE! errors).

## Acceptance Criteria

- Workbook contains 4 sheets: Transactions, Monthly Summary, P&L Statement, Dashboard.
- Transactions sheet has formatted table with 200 rows, currency formatting, date formatting, alternating row colors, and frozen header.
- Monthly Summary uses SUMPRODUCT formulas (not hardcoded values) to compute revenue, expenses, net income per month.
- Monthly Summary has conditional formatting on Margin % column (green ≥20%, yellow 10-20%, red <10%).
- P&L Statement follows standard income statement layout with Revenue, Cost of Revenue, Gross Profit, Operating Expenses, Operating Income sections.
- P&L amounts are SUMPRODUCT formulas referencing Transactions sheet with quarter-specific date criteria.
- FY 2024 column sums Q1-Q4 values (not re-querying raw data).
- Dashboard contains 4 charts: clustered bar (revenue vs expenses), line (net income trend), pie (expense breakdown), bar (quarterly revenue).
- All formulas use cell references; no Python-computed hardcoded values in formula cells.
- Financial formatting: currency with `$#,##0.00`, negatives in parentheses, percentages as `0.0%`, years as text not comma-separated numbers.
- Color coding: blue text for input references, black for formulas, bold subtotal rows with borders.
