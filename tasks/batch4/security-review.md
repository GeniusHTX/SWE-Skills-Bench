# Task: Conduct Security Review and Harden Baby Buddy Application

## Background

Baby Buddy (https://github.com/babybuddy/babybuddy) is a Django-based child-care tracking application that handles sensitive personal data including feeding schedules, sleep records, and health information. A security audit has identified several areas where the application needs hardening: user input handling in API endpoints, authentication token management, sensitive data exposure in error responses, and missing rate limiting on key endpoints.

## Files to Create/Modify

- `babybuddy/settings/base.py` (modify) — Tighten security-related Django settings (session cookies, CSRF, SECURE headers)
- `api/views.py` (modify) — Add input validation and sanitize error responses in the REST API views
- `api/serializers.py` (modify) — Add field-level validation constraints to prevent oversized or malformed input
- `babybuddy/middleware.py` (create) — Implement rate-limiting middleware for authentication and data-mutation endpoints
- `core/views.py` (modify) — Remove sensitive data leakage from error handlers and ensure proper authorization checks

## Requirements

### Authentication and Session Security

- Session cookies must be marked `HttpOnly`, `Secure`, and `SameSite=Lax` (or `Strict`)
- CSRF protection must be enabled for all state-changing endpoints; the CSRF cookie must also be `Secure`
- Authentication failure responses must not reveal whether a username exists in the system
- API token authentication must enforce a maximum token age; expired tokens must be rejected with a `401` status

### Input Validation

- All API serializer fields that accept string input must enforce a `max_length` constraint appropriate to the data type (e.g., notes ≤ 1024 characters, names ≤ 255 characters)
- Numeric fields (e.g., `amount`, `duration`) must have minimum and maximum bounds that reject physiologically implausible values
- Date/time fields must reject dates in the future beyond a small tolerance (5 minutes) for clock skew
- File upload endpoints (if any) must restrict accepted MIME types and enforce a maximum file size of 5 MB

### Error Response Sanitization

- HTTP 500 responses must return a generic error message; stack traces, database details, and internal paths must never appear in the response body
- Validation error messages must describe the constraint violated without echoing back raw user input verbatim
- Django `DEBUG` must be `False` in production settings; a `DEBUG = True` setting must not be present in the base settings file

### Rate Limiting

- Login and token-generation endpoints must be rate-limited to a maximum of 10 requests per minute per IP address
- Data-creation endpoints (`POST` to feeding, sleep, diaper-change resources) must be rate-limited to 60 requests per minute per authenticated user
- Requests exceeding the limit must receive a `429 Too Many Requests` response with a `Retry-After` header

### Sensitive Data Handling

- Log output must not include passwords, tokens, or full request bodies containing personal child data
- API list endpoints must not expose internal database IDs of other users' records; responses must be scoped to the authenticated user's data
- The `User` serializer must exclude password hashes and email addresses from non-admin responses

### Expected Functionality

- An unauthenticated `POST` to `/api/feedings/` returns `401` with no data leakage about existing records
- A login attempt with a valid username but wrong password returns the same error message as a login attempt with a nonexistent username
- Submitting a feeding note with more than 1024 characters returns `400` with a validation message
- Submitting a sleep record with a start time 2 days in the future returns `400`
- After 10 rapid failed login attempts from the same IP, the 11th returns `429` with a `Retry-After` header
- An HTTP 500 triggered by a database error returns `{"detail": "An unexpected error occurred."}` with no stack trace
- A non-admin user querying `/api/users/` sees only their own user record, with no password hash or email field

## Acceptance Criteria

- Session and CSRF cookies are configured with `HttpOnly`, `Secure`, and `SameSite` attributes in base settings
- All API serializer string fields enforce `max_length` and numeric fields enforce `min_value`/`max_value`
- Rate limiting is applied to authentication and data-mutation endpoints, returning `429` when thresholds are exceeded
- Error responses for 4xx and 5xx status codes contain no stack traces, internal paths, or raw database error messages
- API responses are scoped to the authenticated user's data; the User serializer omits sensitive fields for non-admin callers
- Login failure messages are identical regardless of whether the username exists
