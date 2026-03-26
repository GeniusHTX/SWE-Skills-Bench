# Task: Add User Behavior Analytics Event Definitions to Metabase

## Background

Metabase (https://github.com/metabase/metabase) is an open-source business intelligence tool. The frontend codebase uses Snowplow-based analytics to track user interactions. New event type definitions and tracking functions need to be added for key user behavior events that are currently untracked.

## Files to Create/Modify

- `frontend/src/metabase-types/analytics/events.ts` (modify) — Add new event type definitions to the analytics union type
- `frontend/src/metabase/analytics/tracking.ts` (modify) — Add tracking function wrappers (`trackFeatureDiscovery`, `trackNavigationAction`, `trackContentCreation`)

## Requirements

### Event Type Definitions

- Define TypeScript event types for the following three user interaction events:
  1. `feature_discovery_triggered` — fired when a user opens or interacts with a feature discovery prompt (carries `feature_name: string` and `source: string`)
  2. `navigation_tab_clicked` — fired when a user clicks a main navigation tab (carries `tab_name: string` and `previous_tab: string`)
  3. `content_created` — fired when a user creates a new question, dashboard, or model (carries `content_type: "question" | "dashboard" | "model"` and `content_id: number`)
- Each event type must use the project's standard event validation pattern
- Event names must follow snake_case naming conventions
- Add new events to the appropriate union type so they are type-checked

### Tracking Functions

- Create tracking function wrappers for each new event
- Functions must follow the project's naming convention (camelCase with `track` prefix)
- Use the project's core tracking utility for dispatching events

### Integration

- Call the tracking functions at the appropriate user interaction points in the UI components
- TypeScript compilation must succeed with no type errors

## Expected Functionality

- New events fire when users perform the specified interactions
- All event types are properly typed and validated at compile time
- Events carry appropriate contextual metadata (target IDs, triggered-from locations)

## Acceptance Criteria

- The codebase defines the three required analytics events: `feature_discovery_triggered`, `navigation_tab_clicked`, and `content_created`.
- Each event is part of the project's typed analytics event system and follows the established validation pattern.
- Tracking wrapper functions exist for all three events and expose the expected typed payload fields.
- The relevant UI interaction points dispatch these events when the associated user action occurs.
- Event names and payloads remain type-safe and compile cleanly with the surrounding TypeScript code.
