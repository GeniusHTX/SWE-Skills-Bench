# Task: Implement a Low-Stock Alert Feature in Saleor

## Background

Saleor (https://github.com/saleor/saleor) is a Django-based e-commerce platform. A new feature is needed to monitor product stock levels and generate alerts when inventory falls below configurable thresholds, enabling warehouse managers to take timely replenishment action.

## Files to Create/Modify

- `saleor/warehouse/models.py` (modify) — Add `StockAlert` and `StockAlertConfig` models
- `saleor/warehouse/views.py` (create) — REST API views for alert CRUD and listing
- `saleor/warehouse/serializers.py` (create) — DRF serializers for stock alert data
- `saleor/warehouse/urls.py` (create) — URL routing for stock alert endpoints

## Requirements

### Data Model

- Define a low-stock alert configuration that associates a product variant with a threshold quantity
- Store generated alert records capturing which product triggered the alert, the current stock level, the threshold, and the timestamp

### API Endpoints

- Provide endpoints to configure stock alert thresholds per product variant
- Provide an endpoint to list active (unresolved) low-stock alerts
- Support filtering alerts by warehouse or product category

### Alert Logic

- When stock quantity for a monitored variant drops to or below the configured threshold, generate an alert record
- Avoid generating duplicate alerts for the same variant if an existing unresolved alert exists
- Support resolving/acknowledging alerts

### Django Integration

- Follow Saleor's existing application patterns for models, migrations, and API exposure
- The Django system check must pass after changes

## Expected Functionality

- Configuring a threshold for a product variant and reducing its stock below that threshold creates an alert
- Listing alerts returns all active alerts with relevant product and stock information
- Acknowledging an alert marks it as resolved

## Acceptance Criteria

- Administrators can configure per-variant low-stock thresholds and retrieve the current active alert list.
- When inventory drops to or below the configured threshold, an unresolved low-stock alert is created automatically.
- Duplicate unresolved alerts are not created for the same product variant and threshold breach.
- Alerts can be filtered by warehouse or product category and can also be acknowledged or resolved.
- Invalid references or invalid threshold values are rejected with appropriate API validation behavior.
