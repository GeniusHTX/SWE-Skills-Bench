# Task: Add Dashboard Subscription Analytics Events to Metabase

## Background

Metabase's frontend uses a Snowplow-based analytics system to track user interactions. A new set of analytics events is needed to capture how users interact with dashboard subscriptions — creating, editing, deleting, and sending test subscriptions. These events must be defined as TypeScript types, registered in the analytics event union, and wired up with tracking functions that fire at the appropriate UI interaction points.

## Files to Create/Modify

- `frontend/src/metabase-types/analytics/event.ts` (modify) — Add the `DashboardSubscriptionEvent` type definition with all event variants
- `frontend/src/metabase-types/analytics/schema.ts` (modify) — Register the new event type in the analytics event union type
- `frontend/src/metabase/lib/analytics.ts` (modify) — Add tracking functions for dashboard subscription events using `trackSimpleEvent` and `trackSchemaEvent`
- `frontend/src/metabase/dashboard/components/DashboardSubscriptionPanel/analytics.ts` (new) — Module that exports subscription-specific tracking calls consumed by subscription UI components
- `frontend/src/metabase/dashboard/components/DashboardSubscriptionPanel/analytics.unit.spec.ts` (new) — Unit tests verifying events are dispatched with correct payloads

## Requirements

### Event Type Definitions

- Define a `DashboardSubscriptionEvent` type with the following event variants:
  - `dashboard_subscription_created` — payload: `{ dashboard_id: number; subscription_type: "email" | "slack"; schedule: string; recipient_count: number }`
  - `dashboard_subscription_updated` — payload: `{ dashboard_id: number; subscription_id: number; changed_fields: string[] }`
  - `dashboard_subscription_deleted` — payload: `{ dashboard_id: number; subscription_id: number }`
  - `dashboard_subscription_test_sent` — payload: `{ dashboard_id: number; subscription_type: "email" | "slack"; success: boolean }`
- Each variant must include a `schema` field with value `"dashboard-subscription"` and a `version` field with value `"1-0-0"`

### Schema Registration

- The `DashboardSubscriptionEvent` must be added to the `AnalyticsEvent` union type in `schema.ts`
- The schema name `"dashboard-subscription"` must be registered in the schema registry map

### Tracking Functions

- `trackSubscriptionCreated(dashboardId, subscriptionType, schedule, recipientCount)` — fires `dashboard_subscription_created`
- `trackSubscriptionUpdated(dashboardId, subscriptionId, changedFields)` — fires `dashboard_subscription_updated`; `changedFields` must be a non-empty array or the function must not fire
- `trackSubscriptionDeleted(dashboardId, subscriptionId)` — fires `dashboard_subscription_deleted`
- `trackSubscriptionTestSent(dashboardId, subscriptionType, success)` — fires `dashboard_subscription_test_sent`
- All tracking functions must validate that `dashboardId` is a positive integer; if not, the function must silently return without firing an event

### Expected Functionality

- Calling `trackSubscriptionCreated(42, "email", "daily", 5)` dispatches an event with `event_name: "dashboard_subscription_created"`, `dashboard_id: 42`, `subscription_type: "email"`, `schedule: "daily"`, `recipient_count: 5`, `schema: "dashboard-subscription"`, `version: "1-0-0"`
- Calling `trackSubscriptionUpdated(42, 7, [])` with an empty `changedFields` array does not dispatch any event
- Calling `trackSubscriptionUpdated(42, 7, ["schedule", "recipients"])` dispatches with `changed_fields: ["schedule", "recipients"]`
- Calling `trackSubscriptionCreated(-1, "email", "daily", 5)` with a negative dashboard ID does not dispatch any event
- Calling `trackSubscriptionTestSent(42, "slack", false)` dispatches with `success: false`
- All event types are accessible via the `AnalyticsEvent` union type for type-safe downstream consumers

## Acceptance Criteria

- The `DashboardSubscriptionEvent` type is correctly defined with all four event variants and their payloads
- The event type is added to the `AnalyticsEvent` union and the schema registry
- All four tracking functions dispatch events with correct payloads when given valid inputs
- Tracking functions silently skip dispatch when `dashboardId` is not a positive integer or when `changedFields` is empty (for update events)
- Unit tests verify correct event dispatch for all four event types, validate payload structure, and confirm silent skip behavior for invalid inputs
