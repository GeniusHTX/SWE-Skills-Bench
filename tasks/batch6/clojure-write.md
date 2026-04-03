# Task: Implement Audit Log Query Namespace for Metabase

## Background

Metabase (https://github.com/metabase/metabase) needs an audit log querying capability that allows administrators to search, filter, and analyze audit events programmatically. A new Clojure namespace must be implemented that provides functions for querying audit log entries by various criteria (user, action type, date range, entity) and producing summary statistics. The implementation should follow Metabase's existing patterns for database access and functional composition.

## Files to Create/Modify

- `src/metabase/audit_log/query.clj` (create) — Core namespace with functions for querying, filtering, and summarizing audit log events
- `src/metabase/audit_log/models.clj` (create) — Spec/schema definitions for audit log records and query parameters
- `src/metabase/api/audit_log.clj` (create) — API endpoint definitions for admin access to audit log queries
- `test/metabase/audit_log/query_test.clj` (create) — Unit tests for all query functions with varied inputs and edge cases

## Requirements

### Data Model

- An audit log entry is a map with the following keys:
  - `:id` — positive integer
  - `:user_id` — positive integer (the user who performed the action)
  - `:action` — keyword, one of: `:create`, `:update`, `:delete`, `:login`, `:logout`, `:export`, `:permission-change`
  - `:entity_type` — keyword, one of: `:card`, `:dashboard`, `:collection`, `:user`, `:database`, `:table`
  - `:entity_id` — positive integer (the ID of the affected entity)
  - `:details` — map with action-specific data (e.g., `{:field "name" :old_value "A" :new_value "B"}` for updates)
  - `:timestamp` — java.time.Instant
  - `:ip_address` — string (nullable)

### Query Functions

- `(query-audit-log opts)` — Primary query function accepting an options map:
  - `:user-id` (optional) — filter by user ID
  - `:action` (optional) — filter by action keyword or set of action keywords
  - `:entity-type` (optional) — filter by entity type keyword
  - `:entity-id` (optional) — filter by entity ID (requires `:entity-type` to also be specified)
  - `:start-date` (optional) — java.time.Instant, inclusive lower bound on timestamp
  - `:end-date` (optional) — java.time.Instant, exclusive upper bound on timestamp
  - `:limit` (optional, default 100) — max results to return
  - `:offset` (optional, default 0) — pagination offset
  - `:order-by` (optional, default `[[:timestamp :desc]]`) — sort specification
  - Returns a map with `:results` (sequence of audit entries) and `:total_count` (int).
  - When called with no filters, returns the most recent 100 entries.

- `(count-by-action opts)` — Returns a map of action keyword → count for the given filter criteria (supports `:user-id`, `:entity-type`, `:start-date`, `:end-date`).
  - Example return: `{:create 45, :update 120, :delete 12, :login 200}`.

- `(count-by-user opts)` — Returns a sequence of maps `[{:user_id 1 :count 42} {:user_id 2 :count 15} ...]` sorted by count descending, for the given filter criteria. Accepts `:action`, `:entity-type`, `:start-date`, `:end-date`, `:limit` (default 10).

- `(entity-history entity-type entity-id)` — Returns all audit log entries for a specific entity, ordered by timestamp descending. Equivalent to `(query-audit-log {:entity-type entity-type :entity-id entity-id :order-by [[:timestamp :desc]]})`.

### API Endpoints

- `GET /api/audit-log` — calls `query-audit-log` with query parameters mapped from: `user_id`, `action`, `entity_type`, `entity_id`, `start_date`, `end_date`, `limit`, `offset`. Requires admin permissions.
- `GET /api/audit-log/summary` — calls `count-by-action` and returns the action count map. Requires admin permissions.
- `GET /api/audit-log/top-users` — calls `count-by-user` and returns the top N active users. Accepts `limit` query param. Requires admin permissions.

### Validation

- `:entity-id` without `:entity-type` → throw `ex-info` with `{:status-code 400 :message "entity-id requires entity-type"}`.
- `:start-date` after `:end-date` → throw `ex-info` with `{:status-code 400 :message "start-date must be before end-date"}`.
- `:limit` must be between 1 and 10000; values outside this range → throw `ex-info` with message `"limit must be between 1 and 10000"`.
- Unknown `:action` keywords → throw `ex-info` with message listing valid actions.

### Expected Functionality

- `(query-audit-log {:action :login :limit 10})` → returns the 10 most recent login events.
- `(query-audit-log {:user-id 5 :start-date #inst "2026-01-01" :end-date #inst "2026-02-01"})` → returns user 5's actions in January 2026.
- `(query-audit-log {:entity-id 42})` without `:entity-type` → throws validation error.
- `(count-by-action {:start-date #inst "2026-03-01"})` → returns `{:create 12 :update 45 :login 88 ...}` for March 2026.
- `(count-by-user {:action :update :limit 5})` → returns top 5 users by update count.
- `(entity-history :dashboard 7)` → returns all audit entries for dashboard 7, newest first.
- `GET /api/audit-log?action=login&limit=5` → JSON response with 5 most recent login entries, requires admin auth.
- `GET /api/audit-log` without admin auth → 403 Forbidden.

## Acceptance Criteria

- The `query-audit-log` function supports all specified filter options and returns correctly paginated results with total count.
- The `count-by-action` and `count-by-user` aggregation functions return correct counts matching the applied filters.
- `entity-history` returns a complete chronological history for a specific entity.
- Validation rejects invalid parameter combinations (missing entity-type, reversed date range, out-of-range limit) with descriptive error messages.
- API endpoints require admin permissions and map query parameters to the underlying Clojure functions correctly.
- All functions compose cleanly — filters can be combined freely (e.g., user + action + date range).
- Tests cover each function with multiple filter combinations, pagination, edge cases (empty results, single result), and validation error cases.
