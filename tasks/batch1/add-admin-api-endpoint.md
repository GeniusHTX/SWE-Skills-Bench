# Task: Create audit_logs Admin API Endpoint for Ghost CMS

## Background

We need to add an `audit_logs` resource endpoint to the Ghost Admin API, allowing administrators to query recent user operation records for security and compliance purposes.

## Files to Create/Modify

* `ghost/core/core/server/api/endpoints/audit-logs.js` - API endpoint implementation
* `ghost/core/core/server/models/audit-log.js` - Data model
* `ghost/core/core/server/web/api/endpoints/admin/routes.js` - Register endpoint
* `ghost/core/test/e2e-api/admin/audit-logs.test.js` - Test cases

## Requirements

### Model (audit-log.js)

* `id`: ObjectId (Primary Key)
* `userId`: ObjectId (Reference to User)
* `action`: String (e.g., "post.created", "user.login")
* `context`: JSON (Additional metadata)
* `createdAt`: DateTime

### API Endpoints

* `GET /ghost/api/admin/audit_logs/` - Browse with pagination (limit/page)
* `GET /ghost/api/admin/audit_logs/:id` - Read single record

### Implementation (audit-logs.js)

* **browse** : Support limit and page pagination parameters
* **read** : Query single record by id
* Proper permission checking (admin only)

## Expected Functionality

1. Authenticated owner/admin users receive 200 OK with audit_logs array in response body
2. Unauthenticated requests return 401 Unauthorized
3. Pagination parameters (limit, page) work correctly

## Acceptance Criteria

* API endpoints respond with correct status codes
* Response body contains `audit_logs` field with proper structure
* Permission checking works (admin-only access)
* Pagination functions as specified
