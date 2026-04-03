# Task: Add Snowplow Analytics Events for Dashboard Filter Interactions in Metabase

## Background

Metabase (https://github.com/metabase/metabase) uses Snowplow for product analytics tracking. The dashboard filter feature currently lacks analytics instrumentation — the team cannot measure how users interact with dashboard filters (apply, clear, save as default, toggle visibility). Analytics events need to be wired into the dashboard filter UI components to track these interactions.

## Files to Create/Modify

- `frontend/src/metabase-types/analytics/event.ts` (modify) — Add new event type definitions for dashboard filter interactions
- `frontend/src/metabase/dashboard/analytics.ts` (create) — Tracking function wrappers for each dashboard filter event
- `frontend/src/metabase/dashboard/components/DashboardFilterBar.tsx` (modify) — Wire tracking calls into filter apply and clear user interactions
- `frontend/src/metabase/dashboard/components/DashboardFilterPanel.tsx` (modify) — Wire tracking calls into filter save-as-default and visibility toggle interactions

## Requirements

### Event Type Definitions

- Define the following event types in `event.ts` using the `ValidateEvent` generic:

  - `DashboardFilterAppliedEvent`:
    ```typescript
    { event: "dashboard_filter_applied"; target_id: number; event_detail: string }
    ```
    - `target_id`: the dashboard ID
    - `event_detail`: the filter parameter name (e.g., `"category"`, `"date_range"`)

  - `DashboardFilterClearedEvent`:
    ```typescript
    { event: "dashboard_filter_cleared"; target_id: number }
    ```
    - `target_id`: the dashboard ID

  - `DashboardFilterAllClearedEvent`:
    ```typescript
    { event: "dashboard_filter_all_cleared"; target_id: number; event_detail: string }
    ```
    - `event_detail`: the count of filters that were cleared (as a string, e.g., `"3"`)

  - `DashboardFilterDefaultSavedEvent`:
    ```typescript
    { event: "dashboard_filter_default_saved"; target_id: number; event_detail: string }
    ```
    - `event_detail`: number of filters with default values set (as a string)

  - `DashboardFilterVisibilityToggledEvent`:
    ```typescript
    { event: "dashboard_filter_visibility_toggled"; target_id: number; result: string }
    ```
    - `result`: `"visible"` or `"hidden"`

- Add all five types to the `DashboardEvent` union type.

### Tracking Functions

- Create the following functions in `dashboard/analytics.ts`, each calling `trackSimpleEvent()`:

  - `trackDashboardFilterApplied(dashboardId: number, parameterName: string)` — fires `dashboard_filter_applied`.
  - `trackDashboardFilterCleared(dashboardId: number)` — fires `dashboard_filter_cleared`.
  - `trackDashboardFilterAllCleared(dashboardId: number, filterCount: number)` — fires `dashboard_filter_all_cleared`.
  - `trackDashboardFilterDefaultSaved(dashboardId: number, defaultCount: number)` — fires `dashboard_filter_default_saved`.
  - `trackDashboardFilterVisibilityToggled(dashboardId: number, isVisible: boolean)` — fires `dashboard_filter_visibility_toggled` with `result` set to `"visible"` or `"hidden"`.

### Integration Points

- In `DashboardFilterBar.tsx`:
  - Call `trackDashboardFilterApplied` when a user applies a filter value (on the apply/submit action, not on every keystroke).
  - Call `trackDashboardFilterCleared` when a user clears an individual filter.
  - Call `trackDashboardFilterAllCleared` when a user clicks "Clear all filters", passing the count of active filters.

- In `DashboardFilterPanel.tsx`:
  - Call `trackDashboardFilterDefaultSaved` when a user saves filter defaults, passing the number of filters that have a default value.
  - Call `trackDashboardFilterVisibilityToggled` when a user toggles a filter's visibility between shown and hidden.

### Expected Functionality

- User applies a "Category" filter on dashboard #42 → Snowplow receives event `{event: "dashboard_filter_applied", target_id: 42, event_detail: "category"}`.
- User clicks "Clear all" with 3 active filters on dashboard #42 → Snowplow receives `{event: "dashboard_filter_all_cleared", target_id: 42, event_detail: "3"}`.
- User saves 2 filter defaults → Snowplow receives `{event: "dashboard_filter_default_saved", target_id: 42, event_detail: "2"}`.
- User hides a filter → Snowplow receives `{event: "dashboard_filter_visibility_toggled", target_id: 42, result: "hidden"}`.
- Events fire only on explicit user actions, not on page load or programmatic filter changes.

## Acceptance Criteria

- Five new event types are defined in `event.ts` with correct field types and added to the `DashboardEvent` union.
- Five tracking functions in `dashboard/analytics.ts` correctly map arguments to `trackSimpleEvent()` calls.
- Filter apply, clear, clear-all, save-default, and visibility-toggle interactions each fire the corresponding tracking event.
- Event `target_id` always carries the current dashboard's ID.
- Events fire only on user-initiated actions, not on initial load or programmatic changes.
- All event names use snake_case, matching Metabase's existing event naming convention.
