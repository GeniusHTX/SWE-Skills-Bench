# Task: Add Collection Sharing Analytics Events to Metabase Frontend

## Background

Metabase (https://github.com/metabase/metabase) uses Snowplow-based analytics to track user interactions. A new **Collection Sharing** feature is being developed that allows users to share collections with external recipients via email links. Analytics events must be added to track key interactions: sharing a collection, revoking a share, copying a share link, and viewing shared collection settings. All events use the `SimpleEvent` schema pattern and must follow Metabase's existing analytics architecture.

## Files to Create/Modify

- `frontend/src/metabase-types/analytics/event.ts` (modify) — Add new event types: `CollectionShareCreatedEvent`, `CollectionShareRevokedEvent`, `CollectionShareLinkCopiedEvent`, `CollectionShareSettingsViewedEvent`; add these to a new `CollectionShareEvent` union type; add `CollectionShareEvent` to the top-level `SimpleEvent` union
- `frontend/src/metabase-types/analytics/index.ts` (modify) — Export the new event types if needed
- `frontend/src/metabase/collections/analytics.ts` (modify) — Add tracking functions: `trackCollectionShareCreated`, `trackCollectionShareRevoked`, `trackCollectionShareLinkCopied`, `trackCollectionShareSettingsViewed`; each function calls `trackSimpleEvent` with the appropriate event object
- `frontend/src/metabase/collections/components/CollectionSharingModal.tsx` (create) — React modal component that renders sharing UI and calls the tracking functions at appropriate interaction points
- `frontend/src/metabase/collections/components/CollectionSharingModal.unit.spec.tsx` (create) — Unit tests verifying that each user interaction triggers the correct analytics tracking function

## Requirements

### Event Type Definitions

- `CollectionShareCreatedEvent` — Event name: `"collection_share_created"`. Required fields: `event`, `target_id` (collection ID). Optional fields: `event_detail` (share type: `"email"` or `"link"`)
- `CollectionShareRevokedEvent` — Event name: `"collection_share_revoked"`. Required fields: `event`, `target_id` (collection ID)
- `CollectionShareLinkCopiedEvent` — Event name: `"collection_share_link_copied"`. Required fields: `event`, `target_id` (collection ID), `triggered_from` (one of `"modal"`, `"context_menu"`, `"detail_page"`)
- `CollectionShareSettingsViewedEvent` — Event name: `"collection_share_settings_viewed"`. Required fields: `event`, `target_id` (collection ID)
- All event types must use the `ValidateEvent<>` wrapper to enforce schema compliance
- The `CollectionShareEvent` union must combine all four event types
- `CollectionShareEvent` must be added to the existing `SimpleEvent` union type

### Tracking Functions

- Each tracking function in `frontend/src/metabase/collections/analytics.ts` must import `trackSimpleEvent` from `"metabase/lib/analytics"`
- `trackCollectionShareCreated(collectionId: number, shareType: "email" | "link")` — Calls `trackSimpleEvent` with `{ event: "collection_share_created", target_id: collectionId, event_detail: shareType }`
- `trackCollectionShareRevoked(collectionId: number)` — Calls `trackSimpleEvent` with `{ event: "collection_share_revoked", target_id: collectionId }`
- `trackCollectionShareLinkCopied(collectionId: number, triggeredFrom: "modal" | "context_menu" | "detail_page")` — Calls `trackSimpleEvent` with `{ event: "collection_share_link_copied", target_id: collectionId, triggered_from: triggeredFrom }`
- `trackCollectionShareSettingsViewed(collectionId: number)` — Calls `trackSimpleEvent` with `{ event: "collection_share_settings_viewed", target_id: collectionId }`

### Modal Component

- `CollectionSharingModal` receives props: `collectionId: number`, `isOpen: boolean`, `onClose: () => void`
- On modal open, fire `trackCollectionShareSettingsViewed`
- "Share via Email" button click fires `trackCollectionShareCreated` with `shareType: "email"`
- "Copy Link" button click fires `trackCollectionShareLinkCopied` with `triggeredFrom: "modal"`
- "Revoke Access" button click fires `trackCollectionShareRevoked`
- The component must render a testable DOM structure (use `data-testid` attributes)

### Expected Functionality

- Opening the sharing modal tracks `collection_share_settings_viewed` with the collection's ID
- Clicking "Share via Email" tracks `collection_share_created` with `event_detail: "email"`
- Clicking "Copy Link" tracks `collection_share_link_copied` with `triggered_from: "modal"`
- Clicking "Revoke Access" tracks `collection_share_revoked` with the collection's ID
- All events are type-safe — passing invalid field combinations produces TypeScript compile errors

## Acceptance Criteria

- All four event types are defined in `event.ts` using `ValidateEvent<>` and combined into `CollectionShareEvent`
- `CollectionShareEvent` is included in the `SimpleEvent` union type
- All four tracking functions exist in `frontend/src/metabase/collections/analytics.ts` and correctly call `trackSimpleEvent`
- The `CollectionSharingModal` component fires the correct tracking function for each user interaction
- Unit tests verify that each button click and modal open triggers the corresponding tracking function exactly once
- `python -m pytest /workspace/tests/test_analytics_events.py -v --tb=short` passes
