# Task: Implement a Metadata Audit Log System in Metabase Using Clojure

## Background

The Metabase application (https://github.com/metabase/metabase) needs a metadata audit log that records changes to database metadata — when table visibility is toggled, when column descriptions are updated, or when field semantic types change. This system requires new Clojure namespaces for recording audit events, querying the log, and an API endpoint to expose the log data. The implementation should follow Metabase's existing patterns for models, API endpoints, and REPL-driven development.

## Files to Create/Modify

- `src/metabase/models/metadata_audit_log.clj` (create) — Toucan 2 model definition for the `MetadataAuditLog` entity with schema and helper functions
- `src/metabase/api/metadata_audit.clj` (create) — API namespace with endpoints for querying and filtering audit log entries
- `src/metabase/events/metadata_audit.clj` (create) — Event listener that captures metadata changes and writes audit log entries
- `resources/migrations/001_create_metadata_audit_log.sql` (create) — Database migration creating the audit log table

## Requirements

### Data Model

- The `metadata_audit_log` table must have columns: `id` (auto-increment primary key), `user_id` (integer, foreign key to core_user), `entity_type` (varchar, one of `"table"`, `"field"`, `"database"`), `entity_id` (integer), `action` (varchar, one of `"visibility_changed"`, `"description_updated"`, `"semantic_type_changed"`, `"settings_changed"`), `old_value` (text, JSON-encoded previous state), `new_value` (text, JSON-encoded new state), `created_at` (timestamp, defaulting to current time)
- The Toucan 2 model must define `:types` metadata mapping `old_value` and `new_value` to `:json` for automatic serialization/deserialization
- A helper function `(log-change! user-id entity-type entity-id action old-value new-value)` must validate inputs and insert a record

### API Endpoints

- `GET /api/metadata-audit` — returns a paginated list of audit log entries, most recent first
  - Query params: `entity_type` (optional filter), `entity_id` (optional filter), `action` (optional filter), `user_id` (optional filter), `limit` (optional, default 50, max 200), `offset` (optional, default 0)
  - Response: `{ "data": [...entries], "total": <count>, "limit": <n>, "offset": <n> }`
- `GET /api/metadata-audit/:id` — returns a single audit log entry by ID
  - Returns `404` for nonexistent IDs
- Both endpoints require authentication; unauthenticated requests return `401`
- Both endpoints require admin permissions; non-admin requests return `403`

### Event Listener

- Register listeners for Metabase events: `table-update`, `field-update`, `database-update`
- Each listener must compare old and new values of relevant fields and create an audit log entry only if a tracked field actually changed
- For `field-update`: track changes to `description`, `semantic_type`, `visibility_type`
- For `table-update`: track changes to `visibility_type`, `description`
- For `database-update`: track changes to `name`, `settings`
- The listener must capture the current user ID from the request context

### Input Validation

- The `log-change!` function must validate that `entity_type` is one of the allowed values and that `entity_id` is a positive integer; violations must throw `ex-info` with `:status-code 400`
- API query params must reject negative values for `limit` and `offset`
- `limit` values exceeding 200 must be clamped to 200

### Expected Functionality

- After an admin changes a field's `semantic_type` from `type/Name` to `type/Email` via the existing Metabase API, querying `GET /api/metadata-audit?entity_type=field&entity_id=42` returns an entry with `action: "semantic_type_changed"`, `old_value: {"semantic_type": "type/Name"}`, `new_value: {"semantic_type": "type/Email"}`
- After toggling a table's visibility, the audit log contains an entry with `action: "visibility_changed"` and the old/new visibility values
- If a field update changes only `description` but not `semantic_type`, only one audit entry is created for `description_updated`
- If a field update changes nothing tracked, no audit entry is created
- `GET /api/metadata-audit?limit=5&offset=10` returns at most 5 entries starting from the 11th most recent

## Acceptance Criteria

- The migration SQL creates the `metadata_audit_log` table with all specified columns and constraints
- The Toucan 2 model correctly serializes/deserializes `old_value` and `new_value` as JSON
- `log-change!` validates inputs and inserts records; invalid inputs raise appropriate errors
- Event listeners detect changes to the tracked fields and create audit log entries only when values differ
- API endpoints return correctly paginated, filtered results with proper authentication and authorization checks
- Non-admin users receive `403` when accessing audit endpoints; unauthenticated requests receive `401`
