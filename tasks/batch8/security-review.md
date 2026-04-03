# Task: Conduct Security Review and Apply Fixes to Baby Buddy Django Application

## Background

Baby Buddy (https://github.com/babybuddy/babybuddy) is an open-source Django application for tracking infant care activities (feedings, diaper changes, sleep, tummy time). It exposes a Django REST Framework API under `api/`, uses Django's built-in auth system, and stores sensitive child health data. The application needs a security review focusing on the API layer, authentication/authorization configuration, and core data access patterns, with concrete fixes applied for any identified vulnerabilities.

## Files to Create/Modify

- `api/views.py` (modify) — API viewsets; review and fix authorization enforcement, queryset scoping, and input validation
- `api/serializers.py` (modify) — DRF serializers; review and fix mass-assignment vulnerabilities, field exposure, and input sanitization
- `api/filters.py` (modify, if present) — API filter backends; review for injection via filter parameters
- `babybuddy/settings/base.py` (modify) — Django settings; review and fix security-related settings (CSRF, session, CORS, SECURE_* headers, DEBUG, SECRET_KEY handling, ALLOWED_HOSTS)
- `babybuddy/middleware.py` (modify, if applicable) — Custom middleware; review authentication bypass paths
- `core/models.py` (modify) — Core data models (Child, Feeding, Sleep, DiaperChange, etc.); review field constraints and data validation
- `core/views.py` (modify) — Core views; review for authorization gaps, IDOR, and XSS in template rendering
- `SECURITY_REPORT.md` (create) — Structured security report documenting all findings with severity, affected file, description, and remediation applied

## Requirements

### Authentication and Session Security

- Verify that all API endpoints under `api/` require authentication; unauthenticated requests must receive HTTP 401 or 403
- Verify that Django session cookies are configured with `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SECURE = True` (in production), and `SESSION_COOKIE_SAMESITE = "Lax"` or `"Strict"`
- Verify that CSRF protection is active for all state-changing web views; API endpoints using token auth may exempt CSRF but must not leave session-auth API paths unprotected
- `SECRET_KEY` must not be hardcoded in settings files; it must be loaded from an environment variable with a validation check that raises an error if missing in production

### Authorization and Data Access Control

- All API viewsets must scope querysets to the authenticated user's data — a user must not be able to read, update, or delete another user's child records or associated care entries
- Verify that object-level permissions are enforced, not just list-level filtering; accessing `/api/children/{id}/` with another user's child ID must return 403 or 404
- The `Child`, `Feeding`, `Sleep`, `DiaperChange`, `TummyTime`, `Note`, and `Temperature` models must have foreign-key relationships that enable per-user data isolation
- Admin-only operations (e.g., user management) must check `is_staff` or appropriate permission classes

### Input Validation and Injection Prevention

- All DRF serializer fields must have explicit validation: `DateTimeField` must reject far-future dates (e.g., > 1 year from now), `CharField` fields must have `max_length` constraints, numeric fields must have `min_value`/`max_value` bounds
- Template-rendered user content (child names, notes) must be auto-escaped; verify that no `|safe` or `mark_safe()` is used on user-supplied data without sanitization
- Raw SQL queries, if any, must use parameterized queries; verify Django ORM usage does not contain `.raw()` or `.extra()` calls with string interpolation
- API filter parameters must be validated against an allowlist of field names to prevent ORM injection via crafted filter keys

### Security Headers and Transport Configuration

- The following Django security settings must be enabled for production: `SECURE_BROWSER_XSS_FILTER`, `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS = "DENY"`, `SECURE_HSTS_SECONDS` (minimum 31536000), `SECURE_SSL_REDIRECT` (controlled by environment variable)
- CORS configuration (if `django-cors-headers` is installed) must not use `CORS_ALLOW_ALL_ORIGINS = True`; if CORS is needed, it must specify an explicit origin allowlist
- DEBUG must be `False` in production and controlled via environment variable

### Rate Limiting

- The API must have rate limiting applied to authentication endpoints (login, token obtain) to prevent brute-force attacks
- Rate limits: maximum 5 failed login attempts per minute per IP, maximum 100 API requests per minute per authenticated user
- Rate limiting must be implemented via DRF throttle classes configured in the REST_FRAMEWORK settings

### Security Report

- Produce `SECURITY_REPORT.md` in the repository root with the following sections: Executive Summary, Findings (each with Severity [Critical/High/Medium/Low], Affected File, Description, Remediation), and Summary Table
- Each finding must reference the specific file and code location
- Findings must cover at minimum: authentication enforcement, authorization/IDOR, input validation, security headers, secrets management, and rate limiting

## Expected Functionality

- An unauthenticated `GET /api/children/` request returns HTTP 401 or 403
- An authenticated user requesting `GET /api/children/{other_user_child_id}/` returns HTTP 403 or 404
- A POST to `/api/feedings/` with a `start` time 2 years in the future is rejected with a validation error
- A POST to `/api/children/` with a `first_name` exceeding the max_length constraint is rejected
- Django security headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`) are present in HTTP responses
- Rapid successive failed login attempts (>5 per minute) are throttled with HTTP 429
- `SECURITY_REPORT.md` exists and contains at least 5 documented findings

## Acceptance Criteria

- All API endpoints require authentication; no anonymous access to child or care data is possible
- Queryset scoping ensures users can only access their own data through the API — no IDOR vulnerabilities exist
- DRF serializers have explicit field-level validation constraints (max_length, date range, min/max values)
- Django security settings (`SESSION_COOKIE_HTTPONLY`, `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS`, `SECURE_HSTS_SECONDS`) are properly configured
- `SECRET_KEY` is loaded from an environment variable, not hardcoded
- Rate limiting is configured on authentication and API endpoints via DRF throttle classes
- No raw SQL with string interpolation exists; all database queries use parameterized ORM calls
- No user-supplied data is marked safe for HTML rendering without sanitization
- `SECURITY_REPORT.md` is present at the repository root with structured findings covering all reviewed areas
