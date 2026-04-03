# Task: Add Dashboard Interaction Tracking Events to Metabase Frontend

## Background

Metabase (https://github.com/metabase/metabase) is an open-source analytics platform. The frontend uses Snowplow for product analytics event tracking. Dashboard interactions — creating dashboards, adding cards, applying filters, entering fullscreen mode, and sharing — currently lack granular tracking events. The task is to instrument key dashboard interaction points with typed analytics events so the product team can understand usage patterns.

## Files to Create/Modify

- `frontend/src/metabase/dashboard/analytics.ts` (create) — Event schema definitions and tracking helper functions for all dashboard interaction events
- `frontend/src/metabase/dashboard/components/DashboardHeader/DashboardHeader.tsx` (modify) — Add tracking calls for dashboard creation, save, enter/exit fullscreen, and share actions
- `frontend/src/metabase/dashboard/components/DashCard/DashCard.tsx` (modify) — Add tracking calls for card add, remove, resize, and move interactions
- `frontend/src/metabase/dashboard/components/DashboardFilter/DashboardFilterBar.tsx` (modify) — Add tracking calls for filter apply, clear, and change events
- `frontend/src/metabase/dashboard/components/DashboardSharingMenu/DashboardSharingMenu.tsx` (modify) — Add tracking calls for public link creation and embedding actions

## Requirements

### Event Schema Definitions

Define TypeScript interfaces for each event with the following structure:

#### `dashboard_created`
- Properties: `dashboard_id` (number), `collection_id` (number | null), `num_cards` (number), `has_filters` (boolean)

#### `dashboard_saved`
- Properties: `dashboard_id` (number), `num_cards` (number), `num_filters` (number), `is_new` (boolean)

#### `dashboard_card_added`
- Properties: `dashboard_id` (number), `card_id` (number), `card_type` ("question" | "text" | "heading" | "link" | "action"), `position` ({col: number, row: number})

#### `dashboard_card_removed`
- Properties: `dashboard_id` (number), `card_id` (number), `card_type` (string)

#### `dashboard_filter_applied`
- Properties: `dashboard_id` (number), `filter_type` ("date" | "category" | "id" | "number" | "text"), `filter_widget_type` (string), `is_default` (boolean)

#### `dashboard_fullscreen_toggled`
- Properties: `dashboard_id` (number), `entered` (boolean), `is_night_mode` (boolean)

#### `dashboard_shared`
- Properties: `dashboard_id` (number), `share_type` ("public_link" | "embed" | "export_pdf"), `has_password` (boolean)

### Tracking Implementation

- Each event must be fired using a centralized `trackDashboardEvent(eventName, properties)` function defined in the analytics module
- The tracking function must validate that all required properties are present before dispatching the event
- Events must include automatic metadata: `timestamp` (ISO 8601), `source` ("dashboard"), and `user_id` (from the current session, or null if unavailable)
- Events must be dispatched to the existing Snowplow tracking infrastructure used by Metabase

### Integration Points

- `dashboard_created` fires when the user confirms creation of a new dashboard (after the first save)
- `dashboard_saved` fires on every dashboard save (both new and existing)
- `dashboard_card_added` fires when a card or text box is added to the dashboard in edit mode
- `dashboard_card_removed` fires when a card is removed in edit mode
- `dashboard_filter_applied` fires when a user applies or changes a dashboard filter
- `dashboard_fullscreen_toggled` fires when entering or exiting fullscreen presentation mode
- `dashboard_shared` fires when a user generates a public link, creates an embed, or exports as PDF

### Quality Constraints

- No tracking event may fire during automated test execution unless explicitly opted in
- Events must not include personally identifiable information (no user names, emails, or query text)
- Events with missing required properties must log a warning to the console and not dispatch to Snowplow
- The analytics module must be tree-shakeable — importing it without calling functions must have zero side effects

## Expected Functionality

- Creating a new dashboard and saving it fires both `dashboard_created` and `dashboard_saved` with correct property values
- Adding a question card to a dashboard fires `dashboard_card_added` with the correct `card_type` of `"question"` and position
- Applying a date filter fires `dashboard_filter_applied` with `filter_type: "date"`
- Entering fullscreen fires `dashboard_fullscreen_toggled` with `entered: true`
- Generating a public share link fires `dashboard_shared` with `share_type: "public_link"`
- Calling `trackDashboardEvent` with missing properties logs a warning and does not dispatch

## Acceptance Criteria

- All seven event types are defined with TypeScript interfaces and fire from their respective UI interaction points
- Each event payload includes the declared properties plus automatic metadata (timestamp, source, user_id)
- Missing required properties result in a console warning and the event is not dispatched
- No PII is included in any event payload
- The analytics module has no side effects on import
- Each integration point fires exactly once per user action (no duplicate events)
