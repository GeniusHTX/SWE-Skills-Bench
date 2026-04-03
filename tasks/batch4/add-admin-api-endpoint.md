# Task: Add Announcements Admin API Endpoint to Ghost

## Background

The Ghost CMS (https://github.com/TryGhost/Ghost) needs a new Admin API resource for managing site-wide announcements. Announcements are short messages displayed to all visitors (e.g., maintenance notices, promotional banners). The new endpoint must follow Ghost's existing API framework conventions, including controller structure, route registration, permission enforcement, and e2e test coverage.

## Files to Create/Modify

- `ghost/core/core/server/api/endpoints/announcements.js` (create) — API controller with `browse`, `read`, `add`, `edit`, and `destroy` methods
- `ghost/core/core/server/web/api/endpoints/admin/routes.js` (modify) — Register routes for the announcements resource
- `ghost/core/core/server/models/announcement.js` (create) — Bookshelf model for the announcements database table
- `ghost/core/test/e2e-api/admin/announcements.test.js` (create) — End-to-end API tests covering all CRUD operations and permission checks

## Requirements

### Controller Structure

- The controller must export an object with `docName: 'announcements'`
- `browse` accepts `page`, `limit`, `order`, and `filter` options and returns a paginated collection
- `read` accepts `id` as a data parameter and returns a single announcement
- `add` accepts a request body containing an `announcements` array with one object having `title` (required, max 255 chars), `content` (required, max 2000 chars), `visibility` (one of `public`, `members`, `paid`), and `active` (boolean, defaults to `true`)
- `edit` accepts `id` and updates the fields provided; `title` and `content` validations still apply
- `destroy` accepts `id` and deletes the announcement, returning `204 No Content`

### Validation

- `title` must be a non-empty string with a maximum length of 255 characters; violations return `422 Unprocessable Entity`
- `content` must be a non-empty string with a maximum length of 2000 characters
- `visibility` must be one of the allowed values (`public`, `members`, `paid`); an invalid value returns `422`
- `id` parameters must match Ghost's ID format (24-character hex string); an invalid format returns a validation error

### Permissions

- All five methods must enforce permissions (`permissions: true` or a custom permission function)
- An unauthenticated request must receive `403 Forbidden`
- A request from an API key with insufficient scope must receive `403 Forbidden`

### Route Registration

- Routes must be registered in the admin routes file following the existing pattern for resource endpoints
- `GET /ghost/api/admin/announcements/` maps to `browse`
- `GET /ghost/api/admin/announcements/:id/` maps to `read`
- `POST /ghost/api/admin/announcements/` maps to `add`
- `PUT /ghost/api/admin/announcements/:id/` maps to `edit`
- `DELETE /ghost/api/admin/announcements/:id/` maps to `destroy`

### Expected Functionality

- `POST /ghost/api/admin/announcements/` with `{"announcements": [{"title": "Maintenance", "content": "Down at 2am", "visibility": "public"}]}` returns `201` with the created announcement including a generated `id`
- `GET /ghost/api/admin/announcements/` returns `{"announcements": [...], "meta": {"pagination": {...}}}`
- `GET /ghost/api/admin/announcements/:id/` with a valid ID returns the single announcement
- `GET /ghost/api/admin/announcements/:id/` with a nonexistent ID returns `404`
- `PUT /ghost/api/admin/announcements/:id/` with `{"announcements": [{"title": "Updated"}]}` returns the updated record
- `DELETE /ghost/api/admin/announcements/:id/` returns `204`
- `POST` with missing `title` returns `422`
- `POST` with `visibility: "invalid"` returns `422`
- Unauthenticated requests to any endpoint return `403`

## Acceptance Criteria

- The `announcements` controller file exists and exports a valid Ghost API controller with `docName`, `browse`, `read`, `add`, `edit`, and `destroy` methods
- All five routes are registered in the admin routes file and map to the correct controller methods
- Each controller method specifies `permissions: true` (or a custom permission handler)
- Input validation rejects missing required fields and out-of-range values with `422` responses
- Unauthenticated and unauthorized requests receive `403`
- E2E tests cover successful CRUD operations, validation failures, and permission denials, and all pass
