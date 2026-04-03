# Task: Add Admin API Endpoint for Managing Bookmarks in Ghost

## Background

Ghost (https://github.com/TryGhost/Ghost) is an open-source publishing platform. The Admin API already exposes CRUD endpoints for resources such as posts, tags, snippets, and recommendations. A new "Bookmarks" feature is needed to let staff users save and organize external URLs with a title, description, and optional tags. This requires a new Admin API endpoint following Ghost's existing controller and routing conventions.

## Files to Create/Modify

- `ghost/core/core/server/api/endpoints/bookmarks.js` (create) — Admin API controller implementing `browse`, `read`, `add`, `edit`, and `destroy` actions for bookmarks.
- `ghost/core/core/server/api/endpoints/index.js` (modify) — Register the new `bookmarks` controller in the endpoint index.
- `ghost/core/core/server/models/bookmark.js` (create) — Bookshelf model defining the `bookmarks` table schema and relationships.
- `ghost/core/core/server/data/schema/schema.js` (modify) — Add the `bookmarks` table definition to the database schema.
- `ghost/core/core/server/services/url/UrlService.js` (modify) — Register bookmarks as a resource type if applicable to URL routing.
- `ghost/core/test/e2e-api/admin/bookmarks.test.js` (create) — End-to-end API tests covering all five actions.

## Requirements

### Bookmark Resource Schema

- Each bookmark must have: `id` (ObjectId), `title` (string, required, max 191 chars), `url` (string, required, valid URL), `description` (string, optional, max 500 chars), `created_at`, `updated_at`, `created_by`.
- A bookmark may be associated with one or more tags (many-to-many via a join table `bookmarks_tags`).

### API Actions

- **browse** `GET /ghost/api/admin/bookmarks/` — Return paginated bookmarks; support `limit`, `page`, `order`, `filter`, and `include=tags` query params.
- **read** `GET /ghost/api/admin/bookmarks/:id/` — Return a single bookmark by ID; support `include=tags`.
- **add** `POST /ghost/api/admin/bookmarks/` — Create a new bookmark; request body must contain `bookmarks: [{ title, url, ... }]`; validate `url` is a well-formed URL.
- **edit** `PUT /ghost/api/admin/bookmarks/:id/` — Update an existing bookmark's `title`, `url`, `description`, or tag associations.
- **destroy** `DELETE /ghost/api/admin/bookmarks/:id/` — Delete a bookmark by ID; return 204 on success.

### Permissions and Validation

- Only authenticated staff users (admin, editor, author roles) may access the bookmarks endpoint.
- `title` and `url` are required on creation; omitting either returns a 422 Validation Error.
- Duplicate `url` values across bookmarks are allowed (different staff may bookmark the same URL).
- Requesting a non-existent bookmark ID returns a 404 Not Found error.

### Expected Functionality

- `POST /ghost/api/admin/bookmarks/` with `{ bookmarks: [{ title: "Example", url: "https://example.com" }] }` → 201 with the created bookmark including `id`, `created_at`, and `created_by`.
- `GET /ghost/api/admin/bookmarks/?include=tags&limit=5` → 200 with a paginated list of up to 5 bookmarks, each including its associated tags.
- `PUT /ghost/api/admin/bookmarks/:id/` with `{ bookmarks: [{ title: "Updated" }] }` → 200 with the updated bookmark.
- `DELETE /ghost/api/admin/bookmarks/:id/` → 204 No Content.
- `POST` with missing `url` field → 422 Validation Error with a message indicating `url` is required.
- `GET /ghost/api/admin/bookmarks/nonexistent-id/` → 404 Not Found.

## Acceptance Criteria

- The five CRUD actions (`browse`, `read`, `add`, `edit`, `destroy`) respond at the expected routes with correct HTTP status codes.
- Bookmark creation validates required fields and rejects requests missing `title` or `url` with a 422 error.
- The `include=tags` query parameter returns associated tag objects embedded in bookmark responses.
- Pagination parameters (`limit`, `page`) correctly limit and offset results in the browse action.
- E2E tests cover all five actions and at least one validation error scenario.
- The Ghost application starts without errors after the changes.
