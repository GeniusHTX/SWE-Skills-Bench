# Task: Implement Typed Analytics Event Tracking System for Metabase Frontend

## Background

Metabase (https://github.com/metabase/metabase) is an open-source business intelligence tool. The frontend needs a typed analytics event tracking system that defines events using a schema registry, provides typed tracking functions, enforces consistent naming conventions, and validates event payloads at development time. This should integrate with Metabase's existing frontend code under the `frontend/src/metabase/` directory.

## Files to Create/Modify

- `frontend/src/metabase/analytics/schema.ts` (create) — Event schema registry with typed event definitions
- `frontend/src/metabase/analytics/tracker.ts` (create) — Type-safe event tracking functions with payload validation
- `frontend/src/metabase/analytics/naming.ts` (create) — Naming convention enforcement (snake_case, required prefixes)
- `frontend/src/metabase/analytics/__tests__/schema.test.ts` (create) — Tests for event schema validation
- `frontend/src/metabase/analytics/__tests__/tracker.test.ts` (create) — Tests for event tracking functions

## Requirements

### Event Schema Registry

- Define a `SimpleEventSchema` type with fields: `name` (string), `category` (one of `"navigation"`, `"interaction"`, `"api"`, `"error"`, `"performance"`), `properties` (record of property names to property definitions)
- Each property definition has: `type` (one of `"string"`, `"number"`, `"boolean"`), `required` (boolean, default true), `description` (string), `enum_values` (optional array of allowed values for string types)
- Implement an `EventRegistry` class that stores schemas and provides: `register(schema)`, `get(name)`, `list(category?)`, `validate(name, payload) -> ValidationResult`
- Registration of a duplicate event name raises `DuplicateEventError`
- Schema names must follow snake_case convention: lowercase letters, digits, and underscores only; must start with a letter

### Event Naming Convention

- All event names must follow the pattern: `{object}_{action}` (e.g., `dashboard_viewed`, `question_created`, `filter_applied`)
- Implement a `validateEventName(name: string) -> NameValidationResult` function that checks:
  - Snake_case format (no uppercase, no hyphens, no spaces)
  - Contains exactly one underscore separating object and action
  - Object is from a predefined set: `dashboard`, `question`, `filter`, `card`, `collection`, `alert`, `user`, `admin`
  - Action is from a predefined set: `viewed`, `created`, `updated`, `deleted`, `clicked`, `applied`, `exported`, `shared`
- Return specific error messages for each violation (e.g., "Event name 'Dashboard-Viewed' must be snake_case")

### Type-Safe Tracking Functions

- Implement a `track(eventName: string, properties: Record<string, unknown>)` function that:
  - Looks up the schema from the registry
  - Validates the properties against the schema: required fields present, types match, enum values valid
  - If valid, dispatches the event (calls a configurable `dispatcher` function)
  - If invalid, throws `EventValidationError` with details of all violations (not just the first)
- Implement a `createTypedTracker<T>(schema: SimpleEventSchema)` function that returns a strongly-typed tracking function specific to that event's property types
- The typed tracker should provide compile-time type safety: missing required properties or wrong types cause TypeScript errors

### Batch Tracking

- Implement `trackBatch(events: Array<{name: string, properties: Record<string, unknown>}>)` that validates and dispatches multiple events
- If any event fails validation, none are dispatched (all-or-nothing); the error includes details for all invalid events
- Provide an `eventBuffer` that queues events and flushes them in batches at a configurable interval (default: 5 seconds) or when the buffer reaches a configurable size (default: 20 events)

### Expected Functionality

- Registering `{name: "dashboard_viewed", category: "navigation", properties: {dashboard_id: {type: "number", required: true}}}` succeeds
- `track("dashboard_viewed", {dashboard_id: 42})` validates and dispatches successfully
- `track("dashboard_viewed", {})` throws `EventValidationError` mentioning `dashboard_id` is required
- `track("dashboard_viewed", {dashboard_id: "not-a-number"})` throws `EventValidationError` mentioning type mismatch
- `validateEventName("DashboardViewed")` returns error about snake_case requirement
- `validateEventName("widget_viewed")` returns error about "widget" not being in the allowed objects list
- Registering `"dashboard_viewed"` twice throws `DuplicateEventError`

## Acceptance Criteria

- `EventRegistry` stores schemas and validates payloads against them correctly
- Duplicate event names are rejected with `DuplicateEventError`
- Event names are validated against snake_case format and allowed object/action sets
- `track()` validates all properties and throws `EventValidationError` listing all violations for invalid payloads
- Required field checks, type checks, and enum value checks all function correctly
- `createTypedTracker` provides TypeScript compile-time type safety for event properties
- `trackBatch` implements all-or-nothing semantics: no events dispatched if any fail validation
- `eventBuffer` queues events and flushes at the configured interval or buffer size
- Tests cover valid events, missing fields, type mismatches, naming violations, batch validation, and buffer flushing
