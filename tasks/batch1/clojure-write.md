# Task: Add Currency Field Conversion to Metabase Query Export

## Background

We need to add currency field conversion functionality to Metabase's query result export module, allowing automatic currency formatting based on site settings.

## Files to Create/Modify

- `src/metabase/query_processor/middleware/currency_formatter.clj` (new)
- `src/metabase/api/dataset.clj` (modify export paths)
- `test/metabase/query_processor/middleware/currency_formatter_test.clj` (new)

## Requirements

### Currency Formatter Middleware

- Read site-currency setting from `src/metabase/models/setting.clj`
- Format columns with type `:type/Currency`
- Apply conversion to result set

### Integration Points

- Call middleware in `POST /api/dataset/csv` export path
- Call middleware in `POST /api/dataset/json` export path

### Conversion Logic

- Support common currency pairs (USD, EUR, CNY, etc.)
- Handle null values gracefully
- Non-currency columns should not be affected

### Expected Functionality

- Currency conversions work correctly (e.g., USD → CNY with proper exchange rate)
- Null values are skipped without raising errors
- Non-currency columns remain unchanged
- Invalid currency configuration falls back to default behavior

## Acceptance Criteria

- Implementation compiles and runs without errors
- All currency conversion scenarios work as specified
- Edge cases are handled appropriately
