# Task: Add Secure Data Export Endpoints to a Django Application

## Background

BabyBuddy (https://github.com/babybuddy/babybuddy) is a Django-based child care tracking application. New REST API endpoints are needed to allow authenticated users to export care records securely. The endpoints must enforce authentication, object-level authorization, input validation, and proper data scoping to prevent unauthorized access.

## Files to Create/Modify

- `api/views.py` (modify) — Add data export view classes/functions for care records
- `api/serializers.py` (modify) — Add serializers for export response data
- `api/urls.py` (modify) — Register new export endpoint URL patterns

## Requirements

### API Endpoints

- Implement export endpoints accessible via the REST API that return filtered records for a specific child
- Accept query parameters for filtering by date range and record type
- Return structured JSON with clearly named fields

### Security

- All endpoints must require authentication
- Users must only access data for children they are authorized to view — enforce object-level permissions
- Input parameters must be validated and sanitized
- Error responses must not leak internal details or stack traces

### Data Serialization

- Use Django REST Framework serializers to control which fields are exposed
- Exclude sensitive internal fields unless explicitly needed

## Expected Functionality

- An authenticated request with valid parameters returns the expected filtered records
- An unauthenticated request returns HTTP 401 or 403
- A request for a child the user is not authorized to view returns HTTP 403 or 404
- Invalid parameters return HTTP 400 with a descriptive error message

## Acceptance Criteria

- Authenticated users can export only the care records belonging to children they are authorized to access.
- Unauthenticated requests are denied and do not expose data.
- Invalid filter parameters are rejected with clear client-facing validation errors.
- Export responses contain only the intended serialized fields and exclude sensitive internal data.
- Authorization failures do not leak internal details about other users' children or records.
