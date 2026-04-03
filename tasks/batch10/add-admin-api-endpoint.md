# Task: Create an Announcements Admin API Endpoint in Ghost

## Background

Ghost CMS needs a new Admin API resource called **Announcements** that allows site administrators to create, list, read, update, and delete site-wide announcement banners. The endpoint must follow Ghost's existing API framework conventions: a controller file with `docName`, method definitions using the pipeline stages (validation → permissions → query), registered routes in the admin router, and e2e-api tests.

## Files to Create/Modify

- `ghost/core/core/server/api/endpoints/announcements.js` (create) — API controller with `docName: 'announcements'` and methods: `browse`, `read`, `add`, `edit`, `destroy`
- `ghost/core/core/server/models/announcement.js` (create) — Bookshelf model for the `announcements` table with fields `id`, `title`, `content`, `visibility`, `starts_at`, `ends_at`, `created_at`, `updated_at`
- `ghost/core/core/server/web/api/endpoints/admin/routes.js` (modify) — Register routes for the announcements resource
- `ghost/core/core/server/data/schema/schema.js` (modify) — Add the `announcements` table definition to the schema
- `ghost/core/test/e2e-api/admin/announcements.test.js` (create) — End-to-end API tests for all five CRUD operations

## Requirements

### Announcements Model

- Table name: `announcements`
- Columns:
  - `id` — `string`, length 24, primary key (ObjectId format)
  - `title` — `string`, length 191, required
  - `content` — `text`, nullable
  - `visibility` — `string`, length 50, default `"public"`, allowed values: `"public"`, `"members"`, `"paid"`
  - `starts_at` — `dateTime`, nullable
  - `ends_at` — `dateTime`, nullable
  - `created_at` — `dateTime`, not nullable
  - `updated_at` — `dateTime`, nullable
- The Bookshelf model in `ghost/core/core/server/models/announcement.js` must set `tableName: 'announcements'` and register itself via `ghostBookshelf.model('Announcement', Announcement)`
- The model must include `created_at` and `updated_at` in its `defaults` or rely on the base model timestamps

### API Controller

- File: `ghost/core/core/server/api/endpoints/announcements.js`
- Must export a controller object typed as `@tryghost/api-framework Controller`
- `docName` must be `'announcements'`

#### browse

- Allowed options: `include`, `filter`, `page`, `limit`, `order`
- Validation: `page` and `limit` accepted but not required
- Permissions: `true` (uses default permission handler)
- Query: calls `models.Announcement.findPage(frame.options)`
- Cache invalidation: `false`

#### read

- Allowed options: `include`, `fields`
- Data params: `id`
- Validation: `id` is required
- Permissions: `true`
- Query: calls `models.Announcement.findOne(frame.data, frame.options)`, must reject with 404 if not found

#### add

- Allowed options: `include`
- Validation:
  - `title` is required
  - `visibility` if provided must be one of `"public"`, `"members"`, `"paid"`
  - If both `starts_at` and `ends_at` are provided, `ends_at` must be after `starts_at`
- Permissions: `true`
- Status code: `201`
- Cache invalidation: `true`
- Query: calls `models.Announcement.add(frame.data.announcements[0], frame.options)`

#### edit

- Allowed options: `include`, `id`
- Validation: `id` is required; `visibility` if provided must be one of `"public"`, `"members"`, `"paid"`; `ends_at` must be after `starts_at` when both are present
- Permissions: `true`
- Cache invalidation: `true`
- Query: calls `models.Announcement.edit(frame.data.announcements[0], frame.options)`

#### destroy

- Allowed options: `id`
- Validation: `id` is required
- Permissions: `true`
- Status code: `204`
- Cache invalidation: `true`
- Query: calls `models.Announcement.destroy(frame.options)`

### Route Registration

- In `ghost/core/core/server/web/api/endpoints/admin/routes.js`, add the following routes using `http()` wrapper:
  - `GET /announcements/` → `api.announcements.browse`
  - `GET /announcements/:id/` → `api.announcements.read`
  - `POST /announcements/` → `api.announcements.add`
  - `PUT /announcements/:id/` → `api.announcements.edit`
  - `DELETE /announcements/:id/` → `api.announcements.destroy`

### Schema Definition

- Add an `announcements` entry to the schema in `ghost/core/core/server/data/schema/schema.js` matching the column definitions above
- The `id` column must use `{type: 'string', maxlength: 24, nullable: false, primary: true}`

### E2E Tests

- File: `ghost/core/test/e2e-api/admin/announcements.test.js`
- Use the existing Ghost test framework (`@tryghost/admin-api-test-utils` or the local agent/test setup used by other e2e-api tests in the same directory)
- Tests must cover:
  - **Browse**: `GET /announcements/` returns HTTP 200 with a JSON body containing `announcements` array and `meta` pagination
  - **Read**: `GET /announcements/:id/` returns HTTP 200 with the matching announcement; requesting a non-existent ID returns HTTP 404
  - **Add**: `POST /announcements/` with valid payload returns HTTP 201; missing `title` returns HTTP 422; invalid `visibility` value returns HTTP 422
  - **Edit**: `PUT /announcements/:id/` with a changed `title` returns HTTP 200 with the updated record
  - **Destroy**: `DELETE /announcements/:id/` returns HTTP 204; subsequent `GET` for the same ID returns HTTP 404
  - **Date validation**: `POST /announcements/` where `ends_at` is before `starts_at` returns HTTP 422

### Expected Functionality

- `POST /ghost/api/admin/announcements/` with `{"announcements": [{"title": "Maintenance Window"}]}` → HTTP 201, body contains the created announcement with generated `id`
- `GET /ghost/api/admin/announcements/` → HTTP 200, body contains `{"announcements": [...], "meta": {"pagination": {...}}}`
- `GET /ghost/api/admin/announcements/{id}/` with a valid ID → HTTP 200 with the single announcement
- `GET /ghost/api/admin/announcements/{id}/` with a non-existent ID → HTTP 404
- `PUT /ghost/api/admin/announcements/{id}/` with `{"announcements": [{"title": "Updated"}]}` → HTTP 200
- `DELETE /ghost/api/admin/announcements/{id}/` → HTTP 204, empty body
- `POST /ghost/api/admin/announcements/` without `title` → HTTP 422 validation error
- `POST /ghost/api/admin/announcements/` with `visibility: "invalid"` → HTTP 422 validation error
- `POST /ghost/api/admin/announcements/` with `ends_at` before `starts_at` → HTTP 422 validation error

## Acceptance Criteria

- The announcements controller file exists at `ghost/core/core/server/api/endpoints/announcements.js` with `docName: 'announcements'` and all five CRUD methods
- The Bookshelf model exists at `ghost/core/core/server/models/announcement.js` and is loadable by Ghost's model loader
- Routes are registered in `ghost/core/core/server/web/api/endpoints/admin/routes.js` and map to the correct controller methods
- `cd ghost/core && yarn test:single test/e2e-api/admin/announcements.test.js` passes with all tests green
- Browse returns paginated results; Read returns a single record or 404; Add returns 201; Edit returns 200; Destroy returns 204
- Missing `title` on Add/Edit and invalid `visibility` values are rejected with 422
- Date constraint (`ends_at` must be after `starts_at`) is enforced on both Add and Edit
- Every controller method has an explicit `permissions` property
