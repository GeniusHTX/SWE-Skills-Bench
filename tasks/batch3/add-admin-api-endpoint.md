# Task: Add a Bookmarks Admin API Endpoint to Ghost CMS

## Background

Ghost (https://github.com/TryGhost/Ghost) is an open-source publishing platform built on Node.js. The project needs a new Admin API endpoint for managing article bookmarks — allowing authenticated users to bookmark posts, list their bookmarks, and remove bookmarks. This endpoint must follow Ghost's existing controller, routing, and testing patterns in the `ghost/core/` directory.

## Files to Create/Modify

- `ghost/core/core/server/api/endpoints/bookmarks.js` (create) — Bookmarks API controller with CRUD actions
- `ghost/core/core/server/models/bookmark.js` (create) — Bookmark model with database schema and relations
- `ghost/core/core/server/web/api/endpoints/admin/routes.js` (modify) — Register bookmark routes
- `ghost/core/core/server/data/schema/schema.js` (modify) — Add bookmarks table to the database schema
- `ghost/core/test/e2e-api/admin/bookmarks.test.js` (create) — E2E tests for the bookmarks API

## Requirements

### Database Schema

- Add a `bookmarks` table with columns:
  - `id` — primary key (UUID format following Ghost convention using ObjectId)
  - `user_id` — foreign key to `users` table (required)
  - `post_id` — foreign key to `posts` table (required)
  - `created_at` — timestamp, auto-set on creation
  - `note` — text field (optional, max 500 characters, for user notes on the bookmark)
- Add unique constraint on `(user_id, post_id)` — a user cannot bookmark the same post twice

### API Controller

- Implement controller actions following Ghost's pattern (using `@tryghost/api-framework`):
  - `browse` — List all bookmarks for the authenticated user; support `?include=post` to include full post data; support `?limit` and `?page` pagination; default sort by `created_at` DESC
  - `read` — Get a single bookmark by ID; return 404 if not found or belongs to another user
  - `add` — Create a bookmark; request body: `{"bookmarks": [{"post_id": "...", "note": "..."}]}`; return 422 if the post does not exist; return 422 if the bookmark already exists (unique constraint)
  - `destroy` — Delete a bookmark by ID; return 404 if not found or belongs to another user
- Each action must validate that the authenticated user can only access their own bookmarks
- Use Ghost's JSDoc conventions for documenting controller methods: `@param`, `@returns`, `@description`

### Routing

- Register routes under `/ghost/api/admin/bookmarks/`:
  - `GET /ghost/api/admin/bookmarks/` → `browse`
  - `GET /ghost/api/admin/bookmarks/:id/` → `read`
  - `POST /ghost/api/admin/bookmarks/` → `add`
  - `DELETE /ghost/api/admin/bookmarks/:id/` → `destroy`
- All routes require admin API authentication (use Ghost's existing admin auth middleware)

### Model

- Implement the `Bookmark` model extending Ghost's base model (`ghostBookshelf.Model.extend`)
- Define `tableName: 'bookmarks'`
- Define relationships: `belongsTo('Post')`, `belongsTo('User')`
- Implement `permittedAttributes()` returning `['id', 'user_id', 'post_id', 'note', 'created_at']`
- Implement `defaultRelations()` to support the `?include=post` option

### Expected Functionality

- `POST /ghost/api/admin/bookmarks/` with `{"bookmarks": [{"post_id": "valid-post-id"}]}` creates a bookmark and returns the bookmark object with status 201
- `POST /ghost/api/admin/bookmarks/` with a non-existent `post_id` returns 422 with error message
- `POST /ghost/api/admin/bookmarks/` with an already-bookmarked post returns 422 with "Bookmark already exists" error
- `GET /ghost/api/admin/bookmarks/?include=post` returns bookmarks with embedded post data
- `GET /ghost/api/admin/bookmarks/:id/` where the bookmark belongs to another user returns 404
- `DELETE /ghost/api/admin/bookmarks/:id/` removes the bookmark and returns 204
- `GET /ghost/api/admin/bookmarks/?limit=5&page=2` returns the second page of 5 bookmarks

## Acceptance Criteria

- The `bookmarks` table schema is defined with correct columns, types, and unique constraint
- API controller implements browse, read, add, and destroy actions with proper authorization (users can only access own bookmarks)
- Invalid post IDs and duplicate bookmarks return 422 with descriptive error messages
- Unauthorized access to other users' bookmarks returns 404
- `?include=post` embeds full post data in bookmark responses
- Pagination works correctly with `limit` and `page` parameters
- Routes are registered under the admin API path with proper authentication middleware
- JSDoc documentation is present on all controller methods
- E2E tests cover all CRUD operations, authorization, validation errors, and pagination
