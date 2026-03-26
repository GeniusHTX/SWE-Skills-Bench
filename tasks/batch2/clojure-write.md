# Task: Add Currency Field Conversion to Metabase Query Result Export

## Background

Metabase (https://github.com/metabase/metabase) is built with Clojure and provides query result export functionality. The export module needs to be extended with a currency field transformation feature that converts monetary values between currencies during export, using configurable exchange rates.

## Files to Create/Modify

- `src/metabase/query_processor/middleware/currency_conversion.clj` (create) — Currency conversion functions with configurable exchange rates
- `src/metabase/query_processor/middleware/format_rows.clj` (modify) — Integrate currency conversion into the export pipeline

## Requirements

### Currency Conversion

- Implement a function that accepts a monetary value, a source currency code, and a target currency code, and returns the converted value
- Support configurable exchange rate data (e.g., loaded from a map or configuration)
- Handle edge cases: unknown currency codes, zero amounts, nil values

### Export Integration

- Integrate the conversion into the existing query result export pipeline so that currency columns can be transformed during export
- The conversion should be triggered by column metadata or annotations indicating a currency field

### Data Integrity

- Converted values must maintain appropriate decimal precision
- The original values should not be mutated — conversion produces new values

## Expected Functionality

- Exporting a query result with currency columns and a target currency setting produces correctly converted values
- Missing exchange rate data for a currency pair results in a clear error or fallback behavior
- Non-currency columns are passed through unchanged

## Acceptance Criteria

- Currency values are converted using the configured source and target currency codes and the provided exchange-rate data.
- Currency conversion is only applied to columns explicitly marked as currency fields, while other columns pass through unchanged.
- Missing exchange rates, unknown currency codes, and nil inputs are handled with clear and predictable behavior.
- Converted values preserve appropriate decimal precision and do not mutate the original exported data.
- The export pipeline can produce output in the requested target currency when the necessary metadata is present.
