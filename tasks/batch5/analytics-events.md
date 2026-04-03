# Task: Implement Analytics Event Tracking for Metabase Dashboard Components

## Background

Metabase (https://github.com/metabase/metabase) is an open-source data analytics platform. The frontend uses a structured analytics event system for tracking user interactions. This task requires adding analytics events to the dashboard editing workflow: tracking when users add/remove cards, resize panels, apply filters, and share dashboards. Events must follow Metabase's existing event schema patterns.

## Files to Create/Modify

- `frontend/src/metabase/dashboard/analytics.ts` (create) — Analytics event definitions: typed event schemas for dashboard interactions using TypeScript interfaces.
- `frontend/src/metabase/dashboard/hooks/use-dashboard-analytics.ts` (create) — React hook `useDashboardAnalytics` that provides typed event-tracking functions for dashboard components.
- `frontend/src/metabase/dashboard/components/DashboardHeader/DashboardHeader.analytics.ts` (create) — Event tracking integration for the dashboard header: share, bookmark, full-screen toggle events.
- `frontend/src/metabase/dashboard/components/DashCard/DashCard.analytics.ts` (create) — Event tracking for card interactions: add, remove, resize, move, click-through events.
- `frontend/src/metabase/dashboard/analytics.unit.spec.ts` (create) — Unit tests for event schemas, hook behavior, and event payload validation.

## Requirements

### Event Schema Definitions

Define TypeScript interfaces for each event type:

```typescript
interface DashboardViewedEvent {
  event: "dashboard_viewed";
  dashboard_id: number;
  card_count: number;
  filter_count: number;
  has_parameters: boolean;
  view_duration_ms?: number;
}

interface DashCardAddedEvent {
  event: "dashcard_added";
  dashboard_id: number;
  card_type: "question" | "text" | "heading" | "link" | "action";
  position: { row: number; col: number };
  size: { width: number; height: number };
}

interface DashCardRemovedEvent {
  event: "dashcard_removed";
  dashboard_id: number;
  card_type: string;
  card_id: number;
}

interface DashCardResizedEvent {
  event: "dashcard_resized";
  dashboard_id: number;
  card_id: number;
  old_size: { width: number; height: number };
  new_size: { width: number; height: number };
}

interface DashboardFilterAppliedEvent {
  event: "dashboard_filter_applied";
  dashboard_id: number;
  filter_type: "date" | "category" | "id" | "number" | "text";
  filter_widget_type: string;
  is_default_value: boolean;
}

interface DashboardSharedEvent {
  event: "dashboard_shared";
  dashboard_id: number;
  share_type: "public_link" | "embed" | "export_pdf";
}
```

### Analytics Hook

- `useDashboardAnalytics(dashboardId: number)` → returns an object with typed tracking functions:
  - `trackView(cardCount, filterCount)` — sends `dashboard_viewed` event.
  - `trackCardAdded(cardType, position, size)` — sends `dashcard_added` event.
  - `trackCardRemoved(cardType, cardId)` — sends `dashcard_removed` event.
  - `trackCardResized(cardId, oldSize, newSize)` — sends `dashcard_resized` event. Only fires if size actually changed.
  - `trackFilterApplied(filterType, widgetType, isDefault)` — sends `dashboard_filter_applied` event.
  - `trackShared(shareType)` — sends `dashboard_shared` event.
- All functions are debounced by event type (300ms) to prevent duplicate events from rapid interactions.
- Each function calls `trackStructEvent` from the analytics service with the structured event payload.

### Integration Points

- **DashboardHeader**: call `trackShared` when the share modal confirms, `trackView` on component mount with a cleanup that records `view_duration_ms`.
- **DashCard**: call `trackCardAdded` when a new card is dropped on the grid, `trackCardRemoved` on delete confirmation, `trackCardResized` on resize end.

### Validation Rules

- `dashboard_id` must be a positive integer.
- `card_type` must be from the allowed set.
- `position.row` and `position.col` must be non-negative integers.
- `size.width` and `size.height` must be positive integers.
- If validation fails, log a warning and skip the event (do not throw).

### Expected Functionality

- Adding a question card at position (0, 0) with size 4×3 → fires `dashcard_added` with `{event: "dashcard_added", dashboard_id: 42, card_type: "question", position: {row: 0, col: 0}, size: {width: 4, height: 3}}`.
- Resizing a card from 4×3 to 6×4 → fires `dashcard_resized` with old and new sizes.
- Resizing a card but releasing at the same size (no change) → no event fired.
- Sharing via public link → fires `dashboard_shared` with `share_type: "public_link"`.
- Rapidly clicking the share button 3 times within 300ms → only one event fires (debounced).

## Acceptance Criteria

- All 6 event types have TypeScript interfaces with correct field types.
- `useDashboardAnalytics` hook returns typed tracking functions that call the analytics service.
- Events are debounced by type (300ms) to prevent duplicate tracking.
- Resize events only fire when the size actually changes.
- Validation rejects invalid payloads and logs a warning without throwing.
- Integration files show correct hook usage in DashboardHeader and DashCard components.
- Tests verify event payload structure, debounce behavior, no-change-skip logic, and validation.
