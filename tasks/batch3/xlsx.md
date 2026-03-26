# Task: Implement a Multi-Sheet Financial Comparison Report Generator in openpyxl

## Background

The openpyxl library (https://github.com/ericgazoni/openpyxl) is a Python library for reading and writing Excel 2010 xlsx/xlsm files. A common use case for openpyxl is generating structured financial reports from raw data. This task requires creating a Python script that reads quarterly revenue data from a source CSV file, processes it into a multi-sheet Excel workbook with summary calculations, year-over-year comparison formulas, conditional formatting, and a chart — all using native Excel formulas rather than pre-computed Python values.

## Files to Create/Modify

- `openpyxl/sample/financial_report.py` (create) — Main script that reads input CSV and generates the formatted multi-sheet Excel workbook
- `openpyxl/sample/sample_revenue.csv` (create) — Sample CSV input file with quarterly revenue data for multiple business units across multiple years
- `openpyxl/tests/test_financial_report.py` (create) — Tests that verify the generated workbook structure, formulas, formatting, and chart presence

## Requirements

### Input Data Format

- The CSV file has columns: `Year`, `Quarter` (Q1–Q4), `BusinessUnit`, `Revenue`, `COGS` (Cost of Goods Sold), `OperatingExpenses`
- The file covers at least 3 business units across at least 2 years (8 rows per business unit per year)
- The script must handle missing rows gracefully (e.g., if Q4 data is not yet available for the current year)

### Workbook Structure

- **Sheet 1 ("Raw Data")**: Import all CSV data starting at cell A1; row 1 is headers; apply `Table` formatting (alternating row colors) with a filter on each column; set column widths proportional to content
- **Sheet 2 ("Summary")**: A pivot-style summary with business units as rows and year-quarter combinations as columns; each cell must contain an Excel formula (e.g., `SUMIFS`) referencing the Raw Data sheet — not a hardcoded Python-calculated value; include a "Gross Profit" row per business unit calculated as `Revenue - COGS` using formulas; include a "Gross Margin %" row calculated as `Gross Profit / Revenue` using formulas; include a "Total" column with `SUM` formulas across all quarters for each metric
- **Sheet 3 ("YoY Comparison")**: For each business unit and quarter, show the year-over-year revenue change as both absolute amount and percentage; formulas must reference cells in the Summary sheet; handle the first year (no prior year) by displaying `"N/A"` using an `IF`/`ISBLANK` guard; include an annual growth rate row using formulas

### Formatting Requirements

- **Headers**: Bold, white text on dark blue background (RGB: 0,51,102), centered alignment
- **Currency cells**: Use number format `$#,##0;($#,##0);"-"` (negative in parentheses, zero as dash)
- **Percentage cells**: Use number format `0.0%`
- **Conditional formatting on Gross Margin %**: Green fill (RGB: 198,239,206) for values ≥ 30%, yellow fill (RGB: 255,235,156) for values between 15% and 30%, red fill (RGB: 255,199,206) for values < 15%
- **Conditional formatting on YoY Change %**: Green font for positive values, red font for negative values
- **Column widths**: Set to at least 15 for currency columns, 12 for percentage columns, 20 for the business unit name column
- **Freeze panes**: Freeze row 1 and column A on all sheets so headers and labels remain visible when scrolling

### Chart

- Add a clustered bar chart on the Summary sheet showing total annual revenue per business unit
- Chart title: "Annual Revenue by Business Unit"
- X-axis: Business unit names
- Data series: One series per year
- Chart dimensions: width 20, height 12 (in chart units)
- Position the chart below the summary data table

### Edge Cases and Validation

- If a business unit has no data for an entire year, the Summary formulas must return 0 (not error)
- If Revenue is zero for a quarter, Gross Margin % formula must not produce `#DIV/0!`; it should display `"-"` or 0%
- The script must validate that the CSV contains all required columns and raise a `ValueError` with a descriptive message if any are missing
- The script must handle non-numeric values in Revenue/COGS/OperatingExpenses columns by skipping the invalid row and logging a warning

### Expected Functionality

- Running the script with the sample CSV produces a workbook with exactly 3 sheets named "Raw Data", "Summary", "YoY Comparison"
- The Raw Data sheet contains all valid CSV rows with table formatting and filters
- The Summary sheet cells contain `SUMIFS` formulas referencing 'Raw Data' — not literal numbers
- Gross Margin % of 0/0 does not produce `#DIV/0!`
- YoY Comparison for the earliest year shows `"N/A"` for all change cells
- Conditional formatting highlights are applied to the correct cell ranges on Summary and YoY Comparison sheets
- The bar chart is present on the Summary sheet with correct series and categories

## Acceptance Criteria

- The generated workbook has three sheets with the specified names and structure
- All calculation cells on the Summary and YoY Comparison sheets contain Excel formulas (not hardcoded values); specifically, `SUMIFS`, `SUM`, `IF`, and division formulas are used
- Currency cells use the `$#,##0;($#,##0);"-"` format and percentage cells use `0.0%`
- Conditional formatting rules are present and correctly applied to Gross Margin % and YoY Change % ranges
- A clustered bar chart titled "Annual Revenue by Business Unit" exists on the Summary sheet with one series per year
- Division-by-zero scenarios are handled in formulas without producing `#DIV/0!` errors
- Missing quarter data and the first year in YoY comparisons are handled gracefully
- The CSV input is validated for required columns, and invalid numeric rows are skipped with a warning
- Freeze panes are set on all three sheets
