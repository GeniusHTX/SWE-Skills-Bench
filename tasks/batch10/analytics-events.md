# Task: Add Snowplow Analytics Events for the Collection Bulk Actions Feature

## Background

Metabase (https://github.com/metabase/metabase) is adding bulk action capabilities to collections, allowing users to select multiple items (questions, dashboards, models) and perform operations like move, archive, and change-visibility in one action. Each of these user interactions needs Snowplow analytics tracking via the existing `SimpleEventSchema` infrastructure to measure feature adoption and success rates.

## Files to Create/Modify

- `frontend/src/metabase-types/analytics/event.ts` (modify) — Add new event type definitions for collection bulk actions
- `frontend/src/metabase/collections/analytics.ts` (new) — Tracking function definitions for bulk action events
- `frontend/src/metabase/collections/components/BulkActionBar.tsx` (modify) — Wire tracking calls into the bulk action UI handlers

## Requirements

### Event Type Definitions

Add the following event types to `frontend/src/metabase-types/analytics/event.ts`:

#### `CollectionBulkSelectStartedEvent`
- `event`: `"collection_bulk_select_started"`
- `triggered_from`: `"collection_list" | "collection_detail"`

#### `CollectionBulkMoveEvent`
- `event`: `"collection_bulk_move_completed"`
- `target_id`: `number | null` (destination collection ID)
- `event_detail`: `"question" | "dashboard" | "model" | "mixed"` (type of items moved, "mixed" if more than one type)
- `result`: `"success" | "failure"`
- `duration_ms`: `number | null`

#### `CollectionBulkArchiveEvent`
- `event`: `"collection_bulk_archive_completed"`
- `event_detail`: `"question" | "dashboard" | "model" | "mixed"`
- `result`: `"success" | "failure"`
- `duration_ms`: `number | null`

#### `CollectionBulkChangeVisibilityEvent`
- `event`: `"collection_bulk_visibility_changed"`
- `event_detail`: `"public" | "private" | "official"`
- `result`: `"success" | "failure"`

#### `CollectionBulkSelectAllEvent`
- `event`: `"collection_bulk_select_all_toggled"`
- `event_detail`: `"selected" | "deselected"`

### Union Type Registration

- Create a `CollectionBulkEvent` union type combining all five event types above
- Add `CollectionBulkEvent` to the `SimpleEvent` union type so the events are recognized by the type system

### Tracking Functions — `frontend/src/metabase/collections/analytics.ts`

- `trackCollectionBulkSelectStarted(triggeredFrom: "collection_list" | "collection_detail")` — calls `trackSimpleEvent` with event name and `triggered_from`
- `trackCollectionBulkMoveCompleted(params: { targetId: number | null; itemType: "question" | "dashboard" | "model" | "mixed"; result: "success" | "failure"; durationMs: number | null })` — calls `trackSimpleEvent` mapping `targetId` → `target_id`, `itemType` → `event_detail`, `result`, `durationMs` → `duration_ms`
- `trackCollectionBulkArchiveCompleted(params: { itemType: "question" | "dashboard" | "model" | "mixed"; result: "success" | "failure"; durationMs: number | null })` — calls `trackSimpleEvent`
- `trackCollectionBulkVisibilityChanged(params: { visibility: "public" | "private" | "official"; result: "success" | "failure" })` — calls `trackSimpleEvent` mapping `visibility` → `event_detail`
- `trackCollectionBulkSelectAllToggled(state: "selected" | "deselected")` — calls `trackSimpleEvent` with `event_detail`

All tracking functions must import `trackSimpleEvent` from `metabase/lib/analytics`.

### Component Integration — `BulkActionBar.tsx`

- Call `trackCollectionBulkSelectStarted` when the bulk selection mode is first activated, passing the current context (`"collection_list"` or `"collection_detail"`)
- Call `trackCollectionBulkMoveCompleted` after the move operation resolves:
  - Capture `Date.now()` before the async operation starts, compute `durationMs` on completion
  - Pass `result: "success"` on success, `result: "failure"` on catch
  - Determine `itemType` from the selected items — `"mixed"` if items contain more than one type
- Call `trackCollectionBulkArchiveCompleted` after archive resolves with the same timing and result pattern
- Call `trackCollectionBulkVisibilityChanged` after visibility change resolves
- Call `trackCollectionBulkSelectAllToggled` when the select-all checkbox is toggled

### Naming Conventions

- Event names must use `snake_case` (e.g., `collection_bulk_move_completed`)
- Type names must use `PascalCase` with `Event` suffix (e.g., `CollectionBulkMoveEvent`)
- Tracking function names must use `camelCase` with `track` prefix (e.g., `trackCollectionBulkMoveCompleted`)

### Field Constraints

- Only use fields defined in `SimpleEventSchema`: `event`, `target_id`, `triggered_from`, `duration_ms`, `result`, `event_detail`
- Do NOT add custom fields outside the schema (e.g., no `item_count`, `source_collection`, or `filter_state`)

### Expected Functionality

- User enters bulk selection mode in a collection → `collection_bulk_select_started` fires with correct `triggered_from`
- User selects 3 questions and 1 dashboard, moves to collection ID 42 (succeeds in 1200ms) → `collection_bulk_move_completed` fires with `target_id: 42`, `event_detail: "mixed"`, `result: "success"`, `duration_ms: 1200`
- Move operation fails due to permission error → `collection_bulk_move_completed` fires with `result: "failure"` and correct `duration_ms`
- User archives 2 models (succeeds) → `collection_bulk_archive_completed` fires with `event_detail: "model"`, `result: "success"`
- User toggles select-all on → `collection_bulk_select_all_toggled` fires with `event_detail: "selected"`

## Acceptance Criteria

- All five event types are defined with `ValidateEvent<>` wrapper in `frontend/src/metabase-types/analytics/event.ts`
- `CollectionBulkEvent` union type exists and is included in the `SimpleEvent` union
- All five tracking functions exist in `frontend/src/metabase/collections/analytics.ts`, each calling `trackSimpleEvent` with correctly mapped fields
- Event names follow `snake_case`, type names follow `PascalCase` + `Event` suffix, function names follow `track` + `camelCase`
- No fields outside `SimpleEventSchema` are passed to `trackSimpleEvent`
- Duration tracking captures timing around async operations with `result` reflecting success or failure
- `itemType` is `"mixed"` when selected items span multiple entity types
- TypeScript compiles with no type errors for the new and modified files
