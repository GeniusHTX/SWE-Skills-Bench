# Task: Add a Dashboard Provisioning Validator to Grafana

## Background

Grafana (https://github.com/grafana/grafana) supports provisioning dashboards from JSON files. A new validation component is needed that checks provisioned dashboard JSON files for common errors — missing required fields, invalid panel configurations, and data source reference consistency — before they are loaded.

## Files to Create

- `pkg/services/provisioning/dashboards/validator.go` — Dashboard JSON validation logic (fields, panels, data source consistency)
- `pkg/services/provisioning/dashboards/validator_test.go` — Unit tests for the validator

## Requirements

### Dashboard Validation

- Validate that each dashboard JSON contains required top-level fields (`title`, `uid`, `panels`)
- Check that the `uid` is unique across all dashboards in the provisioning directory
- Verify that panel IDs within a dashboard are unique and non-negative

### Panel Validation

- Validate each panel has a `type`, `title`, and `gridPos` field
- Check that `gridPos` values (x, y, w, h) are non-negative integers and panels don't exceed the dashboard width (24 units)
- Validate that panel data source references match known data source names or use the `-- Mixed --` placeholder

### Data Source Consistency

- Accept a list of known data source names
- Flag panels referencing unknown data sources
- Support variable-based data source references (e.g., `$datasource`) without flagging them

### Output

- Return a structured validation result listing all errors and warnings per dashboard
- Distinguish between errors (must fix) and warnings (recommended fix)

## Expected Functionality

- Valid dashboards pass validation with no errors
- Invalid dashboards produce specific, actionable error messages
- Variable references in data source fields are not treated as errors

## Acceptance Criteria

- Dashboards missing required top-level fields or invalid panel definitions are rejected with specific validation errors.
- Duplicate dashboard UIDs and duplicate panel IDs are detected reliably.
- Data-source references are checked against known sources while allowing variable-based references and the mixed-source placeholder.
- Validation results distinguish clearly between blocking errors and non-blocking warnings.
- Valid dashboard provisioning files pass through the validator without false positives.
