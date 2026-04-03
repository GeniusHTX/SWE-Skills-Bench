# Task: Add Announcements Admin API Endpoint to Ghost

## Background

Ghost (https://github.com/TryGhost/Ghost) is a professional publishing platform with a comprehensive Admin API. The platform currently lacks a dedicated endpoint for managing site-wide announcements — short dismissable messages displayed to readers (e.g., "We're launching a new podcast next week"). This task adds a new `announcements` resource to the Admin API, including CRUD operations, route registration, and end-to-end API tests.

## Files to Create/Modify

- `ghost/core/core/server/api/endpoints/announcements.js` (create) — Controller defining `browse`, `read`, `add`, `edit`, and `destroy` actions for the announcements resource, using the `@tryghost/api-framework` Controller type
- `ghost/core/core/server/web/api/endpoints/admin/routes.js` (modify) — Register GET, POST, PUT, DELETE routes for `/announcements/` and `/announcements/:id`
- `ghost/core/test/e2e-api/admin/announcements.test.js` (create) — End-to-end tests verifying CRUD operations, permissions, validation errors, and 404 handling
- `ghost/core/core/server/data/schema/schema.js` (modify) — Add the `announcements` table definition with columns: `id` (string, primary key), `title` (string, not nullable), `content` (text, nullable), `visibility` (string, default `'public'`), `starts_at` (dateTime, nullable), `ends_at` (dateTime, nullable), `created_at` (dateTime), `updated_at` (dateTime)
- `ghost/core/core/server/models/announcement.js` (create) — Bookshelf model for the `announcements` table with timestamp handling and visibility filtering

## Requirements

### Data Model

- The `announcements` table must include: `id`, `title`, `content`, `visibility`, `starts_at`, `ends_at`, `created_at`, `updated_at`
- `title` is required and must be between 1 and 191 characters
- `visibility` must be one of: `public`, `members`, `paid`; defaults to `public`
- If both `starts_at` and `ends_at` are provided, `ends_at` must be after `starts_at`; otherwise return a 422 Validation Error
- `id` must follow Ghost's ObjectID format

### API Behavior

- `GET /ghost/api/admin/announcements/` — Returns all announcements ordered by `created_at` descending; supports `?filter=visibility:paid` query parameter
- `GET /ghost/api/admin/announcements/:id` — Returns a single announcement; returns 404 if the ID does not exist
- `POST /ghost/api/admin/announcements/` — Creates a new announcement; request body must include `announcements: [{ title, ... }]` following Ghost's JSON envelope convention
- `PUT /ghost/api/admin/announcements/:id` — Updates the specified announcement; returns 404 for non-existent IDs
- `DELETE /ghost/api/admin/announcements/:id` — Deletes the specified announcement; returns 204 on success; returns 404 for non-existent IDs

### Permissions

- All announcement endpoints require admin-level authentication (session or staff token)
- Unauthenticated requests must receive 403 Forbidden
- The `visibility` field controls which frontend readers see the announcement, not who can manage it via Admin API

### Validation

- Creating an announcement without a `title` returns 422 with a validation error message referencing the `title` field
- Setting `visibility` to an unsupported value (e.g., `"vip"`) returns 422
- Setting `ends_at` before `starts_at` returns 422 with a message indicating the date range is invalid

### Expected Functionality

- POST with `{"announcements": [{"title": "New Podcast", "visibility": "public", "starts_at": "2026-04-01T00:00:00Z", "ends_at": "2026-04-30T23:59:59Z"}]}` creates the announcement and returns it with generated `id`, `created_at`, and `updated_at`
- GET for the created ID returns the announcement object
- PUT updating `title` to "Updated Podcast Announcement" persists the change
- DELETE removes the announcement; subsequent GET returns 404
- POST without `title` returns 422

## Acceptance Criteria

- All CRUD endpoints return the expected HTTP status codes (200, 201, 204, 404, 422) for valid and invalid requests
- The response envelope follows Ghost's standard `{"announcements": [...]}` format
- Unauthenticated requests to any announcement endpoint receive 403
- Date range validation rejects `ends_at` values that precede `starts_at`
- End-to-end tests in `announcements.test.js` pass when run with `cd ghost/core && yarn test:single test/e2e-api/admin/announcements.test.js`
