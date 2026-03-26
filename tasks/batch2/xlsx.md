# Task: Build a Report Generation Engine for openpyxl

## Background

The openpyxl library (https://github.com/ericgazoni/openpyxl) is a Python library for reading and writing Excel files. A report engine module is needed that programmatically generates multi-sheet workbooks with data tables, summary calculations, conditional formatting, and charts.

## Files to Create

- `openpyxl/utils/report_engine.py` — Report generation engine

## Requirements

### Core Function

- Implement a callable that accepts structured input data (e.g., list of records with named fields) and produces a valid `.xlsx` workbook

### Multi-Sheet Layout

- **Data sheet**: Raw data in rows with a styled header row
- **Summary sheet**: Aggregate metrics (totals, averages, counts) derived from the data
- **Chart sheet**: At least one chart (line, bar, or pie) visualizing a trend or distribution

### Conditional Formatting

- Apply conditional formatting rules to at least one range (e.g., highlight cells exceeding a threshold)

### Styling

- Bold headers, reasonable column widths, number formatting for currency or percentages where appropriate

## Expected Functionality

- Given sales records with fields like date, product, quantity, and revenue, the engine produces a workbook with all records in a data sheet, summary metrics in a second sheet, and a chart in a third sheet
- Conditional formatting highlights cells based on data-driven rules
- The output file opens correctly in Excel or LibreOffice Calc

## Acceptance Criteria

- The engine can generate a workbook containing at least a data sheet, a summary sheet, and a chart sheet from structured input records.
- Summary calculations reflect the values present in the raw data sheet accurately.
- Conditional formatting is applied to at least one meaningful range based on data-driven thresholds.
- Headers, numeric formatting, and column sizing produce a workbook that is readable in common spreadsheet tools.
- The resulting workbook can be opened successfully and visually reflects the requested reporting structure.
