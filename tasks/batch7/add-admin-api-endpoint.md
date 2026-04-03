# Task: Create an Admin API Endpoint for Managing Newsletters in Ghost

## Background

Ghost (https://github.com/TryGhost/Ghost) is a headless Node.js CMS for professional publishing. The Admin API, located under `ghost/core/core/server/api/`, provides endpoints for managing content, members, and settings. Ghost supports multiple newsletters for segmented email distribution, but the current newsletter management capabilities need to be extended with a new Admin API endpoint that supports bulk operations — specifically, the ability to archive, unarchive, and reorder newsletters in a single API call.

## Files to Create/Modify

- `ghost/core/core/server/api/endpoints/newsletters-bulk.js` (create) — Admin API endpoint handler for bulk newsletter operations (archive, unarchive, reorder)
- `ghost/core/core/server/services/newsletters/NewsletterBulkService.js` (create) — Service encapsulating bulk operation logic, validation, and data access
- `ghost/core/core/server/web/api/endpoints/admin/middleware.js` (modify) — Register the new endpoint route in the admin API router
- `ghost/core/test/e2e-api/admin/newsletters-bulk.test.js` (create) — End-to-end API tests for the new bulk endpoint

## Requirements

### API Design

- `PUT /ghost/api/admin/newsletters/bulk/` accepts a JSON body with a `bulk` array, where each entry specifies a newsletter `id` and the operation to perform
- Supported operations: `archive` (set status to "archived"), `unarchive` (set status to "active"), `reorder` (set `sort_order` to a given integer)
- The endpoint must be authenticated and require the `Admin` role; requests without valid admin session/token must receive HTTP 403
- The response must return the full list of affected newsletter objects with their updated state

### Request Format

```json
{
  "bulk": [
    { "id": "newsletter-uuid-1", "action": "archive" },
    { "id": "newsletter-uuid-2", "action": "unarchive" },
    { "id": "newsletter-uuid-3", "action": "reorder", "sort_order": 0 },
    { "id": "newsletter-uuid-4", "action": "reorder", "sort_order": 1 }
  ]
}
```

### Validation

- Each entry in the `bulk` array must include a valid `id` (UUID format) and a recognized `action`
- The `reorder` action must include a non-negative integer `sort_order` field; missing or negative values must be rejected with HTTP 422
- If any `id` references a newsletter that does not exist, the entire request must fail with HTTP 404 and identify the missing newsletter ID
- An empty `bulk` array must be rejected with HTTP 422
- An `archive` action on the only remaining active newsletter must be rejected with HTTP 422 (at least one newsletter must remain active)

### Business Logic

- `archive` sets the newsletter's `status` field to `"archived"` and its `visibility` to `"none"`
- `unarchive` sets `status` back to `"active"` and `visibility` to `"members"`
- `reorder` updates the `sort_order` field; sort order values must be unique across all active newsletters after the operation completes
- All operations within a single request must be applied atomically — if any operation fails validation, none of the changes should be persisted

### Error Handling

- Validation errors return HTTP 422 with a JSON body listing each invalid entry and the reason
- Authentication failures return HTTP 403
- Non-existent newsletter IDs return HTTP 404
- Internal errors return HTTP 500 with a generic message (no stack trace)

## Expected Functionality

- `PUT /ghost/api/admin/newsletters/bulk/` with two `archive` actions on valid newsletters → HTTP 200, both newsletters now have `status: "archived"`
- `PUT /ghost/api/admin/newsletters/bulk/` with `archive` on the last active newsletter → HTTP 422 with error "Cannot archive the only active newsletter"
- `PUT /ghost/api/admin/newsletters/bulk/` with a non-existent newsletter ID → HTTP 404 identifying the missing ID
- `PUT /ghost/api/admin/newsletters/bulk/` with `reorder` actions assigning `sort_order: 0` and `sort_order: 1` → HTTP 200, newsletters reflect new sort order
- `PUT /ghost/api/admin/newsletters/bulk/` without admin authentication → HTTP 403
- `PUT /ghost/api/admin/newsletters/bulk/` with empty `bulk` array → HTTP 422

## Acceptance Criteria

- The `PUT /ghost/api/admin/newsletters/bulk/` endpoint handles `archive`, `unarchive`, and `reorder` operations and returns updated newsletter objects
- Validation rejects missing IDs, unrecognized actions, missing `sort_order`, negative `sort_order`, and empty bulk arrays with HTTP 422
- The last-active-newsletter guard prevents archiving the only remaining active newsletter
- All operations within a request are atomic — partial application does not occur on validation failure
- The endpoint is protected by admin authentication and returns HTTP 403 for unauthenticated or non-admin callers
- E2E tests cover each success and error scenario described above
