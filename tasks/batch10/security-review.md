# Task: Perform Security Review and Remediation on Baby Buddy

## Background

Baby Buddy is a Django-based web application for tracking infant care activities (feedings, diaper changes, sleep, tummy time). The application exposes a REST API under `api/`, serves a dashboard with user-submitted data, and manages multi-user authentication. A security audit has identified several categories of vulnerabilities that must be found and fixed: hardcoded secrets, insufficient input validation, potential SQL injection vectors, missing authentication/authorization checks, and cross-site scripting (XSS) risks.

## Files to Create/Modify

- `babybuddy/settings/base.py` (modify) — Remove any hardcoded `SECRET_KEY` value; load it from the environment variable `DJANGO_SECRET_KEY` with a startup check that raises `ImproperlyConfigured` if the variable is absent
- `api/views.py` (modify) — Add input validation on all API view parameters that accept user-supplied data; ensure query parameters used for filtering are validated against allowlists
- `api/serializers.py` (modify) — Add field-level validation to serializers handling user-provided text (e.g., `notes` fields) enforcing maximum length and type constraints
- `core/views.py` (modify) — Add `LoginRequiredMixin` or `@login_required` to any class-based or function-based views that currently expose data without authentication
- `core/models.py` (modify) — Ensure any raw SQL or hand-built QuerySet `.extra()` calls use parameterized queries; replace string interpolation in query construction if present
- `dashboard/templatetags/dashboard_tags.py` (modify) — Audit custom template tags for unescaped output; replace `mark_safe` on user-controlled content with properly escaped rendering
- `babybuddy/settings/base.py` (modify) — Configure security headers: set `SECURE_BROWSER_XSS_FILTER = True`, `SECURE_CONTENT_TYPE_NOSNIFF = True`, `X_FRAME_OPTIONS = "DENY"`, and `SESSION_COOKIE_HTTPONLY = True`

## Requirements

### Secret Management

- `SECRET_KEY` in `babybuddy/settings/base.py` must not contain a hardcoded string value
- The application must read `SECRET_KEY` from the `DJANGO_SECRET_KEY` environment variable
- If `DJANGO_SECRET_KEY` is not set at startup, the application must raise `django.core.exceptions.ImproperlyConfigured` with a descriptive message
- No API keys, tokens, or database passwords may appear as literal strings anywhere in the codebase

### Input Validation

- All API endpoints in `api/views.py` that accept query parameters for date filtering (`date`, `date_min`, `date_max`) must validate the format as ISO 8601 (`YYYY-MM-DD`) and reject malformed values with HTTP 400
- Text fields (`notes`, `name`) accepted by serializers in `api/serializers.py` must enforce a maximum length of 1000 characters
- Child age/weight fields must validate as positive numbers; zero and negative values must be rejected with HTTP 400
- File upload endpoints (if any) must validate file size (≤ 5 MB) and MIME type against an allowlist of image types (`image/jpeg`, `image/png`)

### SQL Injection Prevention

- No QuerySet must use `.extra()` or `.raw()` with string formatting (`%`, `f"..."`, `.format()`) on user-supplied values
- All ORM queries that incorporate user input must use Django's parameterized filter kwargs or `Func` / `Value` expressions
- Any raw SQL in `core/models.py` or management commands must use parameterized placeholders (`%s`) with the parameter list passed separately

### Authentication and Authorization

- Every view under `core/views.py` and `dashboard/views.py` that renders or modifies child/care data must require an authenticated session
- API endpoints in `api/views.py` must enforce `IsAuthenticated` (or a more restrictive custom permission) on all non-public routes
- Users must only be able to access data for children linked to their account; queries must filter by the requesting user's associated children

### XSS Prevention

- Custom template tags in `dashboard/templatetags/dashboard_tags.py` must not call `mark_safe()` on any string that includes user-controlled data (e.g., child name, notes)
- If HTML output is required, user-controlled fragments must be escaped with `django.utils.html.escape()` before being included in the safe string
- The response headers `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`, and `X-Frame-Options: DENY` must be set via Django settings

### Security Settings

- `SESSION_COOKIE_HTTPONLY` must be `True`
- `CSRF_COOKIE_HTTPONLY` must be `True`
- `SECURE_BROWSER_XSS_FILTER` must be `True`
- `SECURE_CONTENT_TYPE_NOSNIFF` must be `True`
- `X_FRAME_OPTIONS` must be `"DENY"`

### Expected Functionality

- Application starts successfully when `DJANGO_SECRET_KEY` is set in the environment
- Application fails fast with `ImproperlyConfigured` when `DJANGO_SECRET_KEY` is missing
- `POST /api/feedings/` with a `notes` field exceeding 1000 characters → HTTP 400 with a validation error
- `GET /api/changes/?date=not-a-date` → HTTP 400 with a descriptive error
- Unauthenticated `GET /dashboard/` → HTTP 302 redirect to login page
- Authenticated user A cannot retrieve child data belonging to user B via the API
- Template rendering of a child whose name contains `<script>alert(1)</script>` does not execute JavaScript in the browser

## Acceptance Criteria

- `SECRET_KEY` is loaded exclusively from the `DJANGO_SECRET_KEY` environment variable; no hardcoded secret strings remain in settings files
- All API endpoints return HTTP 400 for malformed date parameters, oversized text fields, and negative numeric inputs
- No `.extra()` or `.raw()` call in the codebase uses string interpolation on user input
- Every view serving child or care data requires authentication and scopes queries to the requesting user's children
- Custom template tags do not pass unescaped user content to `mark_safe()`
- Django security settings (`SESSION_COOKIE_HTTPONLY`, `CSRF_COOKIE_HTTPONLY`, `SECURE_BROWSER_XSS_FILTER`, `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS`) are configured to their secure values
- The application's existing test suite (`python manage.py test`) continues to pass after all changes
