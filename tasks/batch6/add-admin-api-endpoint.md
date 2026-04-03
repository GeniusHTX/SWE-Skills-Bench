# Task: Add Webhooks CRUD Admin API Endpoint to Ghost

## Background

Ghost CMS (https://github.com/TryGhost/Ghost) provides an Admin API for managing content and settings. A new `/ghost/api/admin/webhooks/` endpoint is needed to allow administrators to manage webhook subscriptions through the Admin API. Webhooks enable external services to receive HTTP callbacks when specific events occur in Ghost (e.g., post published, member created).

## Files to Create/Modify

- `ghost/core/core/server/api/endpoints/webhooks.js` (create) — API controller object defining `browse`, `read`, `add`, `edit`, and `destroy` methods for webhook resources
- `ghost/core/core/server/web/api/endpoints/admin/routes.js` (modify) — Register webhook routes: `GET /webhooks/`, `GET /webhooks/:id/`, `POST /webhooks/`, `PUT /webhooks/:id/`, `DELETE /webhooks/:id/`
- `ghost/core/test/e2e-api/admin/webhooks.test.js` (create) — E2E tests covering all CRUD operations, validation, and permission checks

## Requirements

### API Controller

- The controller `docName` must be `"webhooks"`.
- Five methods must be defined:

#### `browse`
- Returns a paginated list of all webhooks.
- Supports `options`: `page`, `limit`, `order`, `fields`.
- Supports `include` for related data: `integration`.
- Requires admin permission.

#### `read`
- Fetches a single webhook by `id`.
- Supports `options`: `id`.
- Supports `include`: `integration`.
- Returns 404 if the webhook does not exist.
- Requires admin permission.

#### `add`
- Creates a new webhook.
- Required fields in request body:
  - `target_url` (string) — the URL to receive the callback. Must be a valid HTTPS URL.
  - `event` (string) — the Ghost event to subscribe to. Must be one of: `post.published`, `post.unpublished`, `post.deleted`, `page.published`, `page.unpublished`, `page.deleted`, `member.added`, `member.deleted`.
- Optional fields:
  - `name` (string, max 191 characters) — human-readable label.
  - `secret` (string, max 191 characters) — shared secret for HMAC signature verification.
  - `integration_id` (string) — associates the webhook with an integration.
  - `api_version` (string, default `"v5"`) — the API version for payload format.
- Validation:
  - `target_url` must be a valid URL with HTTPS scheme; reject HTTP URLs with error `"target_url must use HTTPS"`.
  - `event` must be from the allowed list; reject others with error `"Invalid event type"`.
  - `name` must not exceed 191 characters.
- Must invalidate the webhook cache after creation.
- Requires admin permission.

#### `edit`
- Updates an existing webhook by `id`.
- Supports updating: `target_url`, `event`, `name`, `secret`, `api_version`.
- Same validation rules as `add`.
- Returns 404 if the webhook does not exist.
- Must invalidate the webhook cache after update.
- Requires admin permission.

#### `destroy`
- Deletes a webhook by `id`.
- Returns 204 No Content on success.
- Returns 404 if the webhook does not exist.
- Must invalidate the webhook cache after deletion.
- Requires admin permission.

### Routes

- `GET /webhooks/` → `browse`
- `GET /webhooks/:id/` → `read`
- `POST /webhooks/` → `add`
- `PUT /webhooks/:id/` → `edit`
- `DELETE /webhooks/:id/` → `destroy`

### Expected Functionality

- `POST /ghost/api/admin/webhooks/` with `{"webhooks": [{"target_url": "https://example.com/hook", "event": "post.published"}]}` → returns 201 with the created webhook including a generated `id` and `created_at`.
- `POST` with `target_url: "http://example.com/hook"` (HTTP, not HTTPS) → returns 422 with validation error `"target_url must use HTTPS"`.
- `POST` with `event: "invalid.event"` → returns 422 with validation error `"Invalid event type"`.
- `GET /ghost/api/admin/webhooks/` → returns paginated list of all webhooks.
- `GET /ghost/api/admin/webhooks/{id}/` → returns the specific webhook; returns 404 for non-existent ID.
- `PUT /ghost/api/admin/webhooks/{id}/` with updated `target_url` → returns 200 with updated webhook.
- `DELETE /ghost/api/admin/webhooks/{id}/` → returns 204; subsequent GET returns 404.
- All endpoints return 403 if called without admin authentication.

## Acceptance Criteria

- An endpoint file defines a controller with `docName: "webhooks"` and five methods (`browse`, `read`, `add`, `edit`, `destroy`).
- Routes are registered in the admin routes file mapping HTTP methods and paths to the corresponding controller methods.
- `target_url` validation rejects non-HTTPS URLs with a clear error message.
- `event` validation restricts event types to the eight allowed values.
- All five operations require admin permissions; unauthenticated or non-admin requests are rejected.
- Cache invalidation is triggered on `add`, `edit`, and `destroy` operations.
- E2E tests verify all five operations including success cases, validation failures, 404 handling, and permission checks.
- Tests pass when run via `cd ghost/core && yarn test:single test/e2e-api/admin/webhooks.test.js`.
