# Task: Add a Webhooks Admin API Endpoint to Ghost

## Background

Ghost's Admin API provides RESTful endpoints for managing content and configuration. A new endpoint is needed to manage webhook registrations — allowing integrations to subscribe to Ghost events (e.g., `post.published`, `member.added`, `page.deleted`). The endpoint must support full CRUD operations, validate webhook configurations, and follow Ghost's established endpoint patterns including authentication, permission checks, and serialization.

## Files to Create/Modify

- `ghost/core/core/server/api/endpoints/webhooks.js` (new) — CRUD handler functions (browse, read, add, edit, destroy) for webhook resources
- `ghost/core/core/server/web/api/endpoints/admin/routes.js` (modify) — Register the `/webhooks/` routes in the admin API router
- `ghost/core/core/server/models/webhook.js` (modify) — Add or verify the Webhook model with required fields and validations
- `ghost/core/test/e2e-api/admin/webhooks.test.js` (new) — End-to-end tests for the webhooks Admin API endpoint

## Requirements

### API Endpoints

- `GET /ghost/api/admin/webhooks/` — List all webhooks, ordered by `created_at` descending; supports `page` and `limit` query parameters (default limit: 15, max: 100)
- `GET /ghost/api/admin/webhooks/:id/` — Retrieve a single webhook by ID; return 404 if not found
- `POST /ghost/api/admin/webhooks/` — Create a new webhook; request body contains `webhooks: [{ event, target_url, name, secret }]`
- `PUT /ghost/api/admin/webhooks/:id/` — Update an existing webhook; only `event`, `target_url`, `name`, and `secret` fields are mutable
- `DELETE /ghost/api/admin/webhooks/:id/` — Delete a webhook; return 204 on success, 404 if not found

### Webhook Model

- Required fields: `event` (string, one of: `post.published`, `post.unpublished`, `post.deleted`, `page.published`, `page.deleted`, `member.added`, `member.deleted`), `target_url` (string, valid HTTPS URL)
- Optional fields: `name` (string, max 191 characters), `secret` (string, max 191 characters, used for HMAC signature verification)
- Auto-generated fields: `id` (ObjectId), `created_at`, `updated_at`, `created_by`
- Validation: `target_url` must be a valid HTTPS URL (HTTP URLs must be rejected with a 422 error); `event` must be one of the allowed event names; duplicate `event + target_url` combinations must be rejected with a 422 error

### Permission and Authentication

- All endpoints require Admin API authentication (staff token or session)
- Only users with the `Owner` or `Administrator` role may access webhook endpoints
- Unauthenticated requests must receive a 401 response; unauthorized roles must receive a 403 response

### Response Format

- Responses follow Ghost's JSON envelope format: `{ "webhooks": [...] }` for browse and `{ "webhooks": [{ ... }] }` for read/add/edit
- Error responses use Ghost's standard error format: `{ "errors": [{ "message": "...", "type": "ValidationError", "context": "..." }] }`
- Browse responses include pagination metadata: `{ "meta": { "pagination": { "page": 1, "limit": 15, "pages": 1, "total": 3 } } }`

### Expected Functionality

- `POST /ghost/api/admin/webhooks/` with `{ "webhooks": [{ "event": "post.published", "target_url": "https://example.com/hook" }] }` → 201 response with the created webhook including auto-generated `id` and `created_at`
- `POST` with `target_url: "http://example.com/hook"` (HTTP, not HTTPS) → 422 response with `ValidationError`
- `POST` with `event: "invalid.event"` → 422 response with `ValidationError`
- `POST` with duplicate `event + target_url` that already exists → 422 response indicating duplicate
- `GET /ghost/api/admin/webhooks/?limit=2&page=1` with 5 total webhooks → response with 2 webhooks and pagination metadata showing `pages: 3, total: 5`
- `PUT /ghost/api/admin/webhooks/:id/` updating `event` to `member.added` → 200 response with updated webhook
- `DELETE /ghost/api/admin/webhooks/:id/` → 204 with empty body; subsequent `GET` by same ID returns 404
- Request without authentication → 401 response

## Acceptance Criteria

- All five CRUD operations (browse, read, add, edit, destroy) are functional at `/ghost/api/admin/webhooks/`
- Routes are correctly registered in the admin API router
- Webhook creation validates `target_url` as HTTPS, `event` against the allowed list, and rejects duplicate `event + target_url` pairs
- Responses follow Ghost's JSON envelope format with correct pagination metadata for browse
- Authentication and role-based permission checks return 401 and 403 respectively for unauthorized requests
- End-to-end tests cover all CRUD operations, validation error cases, pagination, and permission checks
