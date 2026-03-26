# Task: Create an Audit Logs Endpoint in the Ghost Admin API

## Background

Ghost (https://github.com/TryGhost/Ghost) is an open-source publishing platform with a comprehensive Admin API. A new `audit_logs` resource endpoint is needed so administrators can query a record of significant actions performed within the system.

## Files to Create/Modify

- `ghost/core/core/server/api/endpoints/audit-logs.js` (create) — Audit logs API endpoint controller (browse handler)
- `ghost/core/core/server/services/audit-log/index.js` (create) — Audit log service layer (query, filter, paginate)
- `ghost/core/core/server/web/api/endpoints.js` (modify) — Register the new `/audit_logs/` route

## Requirements

### Endpoint Design

- Register a new REST resource under the Admin API namespace
- Support `GET` (browse) operations for retrieving audit log entries
- Support query parameters for filtering by action type, actor, and date range
- Paginate results using Ghost's standard pagination conventions

### Data Model

- Each entry includes: action performed, actor (user or integration), target resource type and ID, timestamp, and optional metadata
- Define the schema so it integrates with Ghost's data layer

### Access Control

- Require Admin API authentication
- Only administrator-level users should be able to access audit logs

### Response Format

- Follow Ghost's existing API response envelope structure

## Expected Functionality

- An authenticated admin GET request returns a paginated list of audit entries
- Filtering by action type returns only matching entries
- Unauthenticated or insufficiently privileged requests are rejected

## Acceptance Criteria

- The Admin API exposes a new `audit_logs` browse endpoint under the existing admin namespace.
- Authenticated administrator requests receive a paginated response containing audit log entries with the required fields and metadata structure.
- Filtering by action type, actor, and date range narrows the returned results correctly.
- Non-admin or unauthenticated requests are rejected with the expected permission behavior.
- The response format matches Ghost's existing Admin API envelope conventions.
