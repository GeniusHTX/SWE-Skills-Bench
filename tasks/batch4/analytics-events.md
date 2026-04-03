# Task: Add Analytics Events for Collection Bookmark Interactions in Metabase

## Background

The Metabase frontend (https://github.com/metabase/metabase) uses Snowplow-based analytics events to track user interactions. The collections feature currently lacks analytics coverage for bookmark-related interactions: creating bookmarks, removing bookmarks, reordering bookmarks, and accessing bookmarked items. These events need to be added following Metabase's typed event system so product teams can measure bookmark feature adoption and usage patterns.

## Files to Create/Modify

- `frontend/src/metabase-types/analytics/event.ts` (modify) — Add TypeScript type definitions for the new bookmark analytics events
- `frontend/src/metabase/collections/analytics.ts` (create) — Tracking function wrappers for bookmark events
- `frontend/src/metabase/collections/components/CollectionBookmark.tsx` (modify) — Integrate bookmark-created and bookmark-removed tracking calls at interaction points
- `frontend/src/metabase/collections/components/BookmarkList.tsx` (modify) — Integrate bookmark-reordered and bookmark-item-clicked tracking calls

## Requirements

### Event Type Definitions

Add the following event types to the analytics event type file:

- `CollectionBookmarkCreatedEvent` — fires when a user bookmarks a collection; includes `target_id` (collection ID) and `triggered_from` (one of `"collection-header"`, `"sidebar"`, `"search-result"`)
- `CollectionBookmarkRemovedEvent` — fires when a user removes a bookmark; includes `target_id` (collection ID) and `triggered_from` (same locations as above)
- `CollectionBookmarkReorderedEvent` — fires when a user drags to reorder their bookmarks; includes `event_detail` indicating the direction (`"moved-up"` or `"moved-down"`)
- `CollectionBookmarkItemClickedEvent` — fires when a user clicks an item in the bookmarks sidebar list; includes `target_id` (item ID) and `event_detail` (item type: `"collection"`, `"dashboard"`, `"question"`)

All four types must use the `SimpleEventSchema` via `ValidateEvent` and use `snake_case` event names prefixed with `collection_bookmark_`.

### Union Type Registration

- Create a `CollectionBookmarkEvent` union type that includes all four event types
- Add `CollectionBookmarkEvent` to the top-level `AnalyticsEvent` union type so the events are recognized by the tracking system

### Tracking Functions

- Each event must have a dedicated tracking function in `frontend/src/metabase/collections/analytics.ts`
- Functions must call `trackSimpleEvent()` from `metabase/lib/analytics`
- Function signatures must accept only the parameters required by their event type (no extra optional fields)
- Parameter types must be strict (literal unions, not plain `string`) matching the event type definitions

### Component Integration

- `CollectionBookmark.tsx`: call the tracking function for bookmark creation inside the handler that fires when a user clicks the bookmark icon to add a bookmark; call the removal tracking function when the icon is clicked to remove an existing bookmark
- `BookmarkList.tsx`: call the reorder tracking function inside the drag-end handler; call the item-clicked tracking function when a bookmark list item is clicked, passing the item's type and ID

### Expected Functionality

- Clicking the bookmark icon on a collection header fires `collection_bookmark_created` with `triggered_from: "collection-header"` and the collection's ID as `target_id`
- Clicking the bookmark icon on an already-bookmarked collection fires `collection_bookmark_removed`
- Dragging a bookmark one position up fires `collection_bookmark_reordered` with `event_detail: "moved-up"`
- Clicking a dashboard item in the bookmark sidebar fires `collection_bookmark_item_clicked` with `event_detail: "dashboard"` and the item's ID as `target_id`
- Calling a tracking function with an incorrect `triggered_from` value causes a TypeScript compilation error

## Acceptance Criteria

- Four new event types are defined in the analytics event type file using `ValidateEvent` and `SimpleEventSchema`
- A `CollectionBookmarkEvent` union type exists and is included in the top-level analytics event union
- Tracking functions in `collections/analytics.ts` accept strictly typed parameters and call `trackSimpleEvent`
- Bookmark creation, removal, reorder, and click interactions in the two component files invoke the correct tracking functions with the correct arguments
- TypeScript compilation succeeds with no type errors across the modified and new files
- Event names follow the `collection_bookmark_*` snake_case naming convention
