# Task: Remediate Security Vulnerabilities in Baby Buddy Application

## Background

Baby Buddy (https://github.com/babybuddy/babybuddy) is a Django-based child-care tracking application that allows parents to log feedings, diaper changes, sleep, and other activities. A security audit has identified several vulnerabilities across the API layer, user management views, session handling middleware, and production settings. These issues must be fixed to harden the application against common web attacks before the next release.

## Files to Create/Modify

- `babybuddy/settings/base.py` (modify) — Harden security-related settings: enforce secure cookie flags, add missing security headers, restrict `ALLOWED_HOSTS` default
- `babybuddy/views.py` (modify) — Fix authorization bypass in user management views (`UserPassword`, `UserDelete`, `UserSettings`) where a non-staff user can modify another user's account by manipulating the URL primary key
- `api/views.py` (modify) — Add rate limiting to the API token authentication endpoint and ensure all ViewSets enforce object-level permission checks
- `api/serializers.py` (modify) — Add input validation to prevent mass-assignment of privileged fields (e.g., `is_staff`, `is_superuser`) through the API
- `babybuddy/middleware.py` (modify) — Fix the `HomeAssistantMiddleware` to validate the `X-Ingress-Path` header value against an allowlist, preventing open-redirect via header injection
- `core/views.py` (modify) — Add CSRF validation and permission checks to data-entry views that accept POST requests for creating `Feeding`, `DiaperChange`, `Sleep`, and `Tummy-Time` records

## Requirements

### Broken Access Control

- The `UserPassword` view at `/users/<pk>/password/` must verify that the requesting user's PK matches the URL PK, or that the requesting user has staff permissions; otherwise return HTTP 403
- The `UserDelete` view at `/users/<pk>/delete/` must enforce the same ownership-or-staff check and must not allow a regular user to delete any other user's account
- The `UserSettings` view at `/users/<pk>/settings/` must restrict access so a user can only update their own settings unless they are staff
- All API ViewSets (`FeedingViewSet`, `SleepViewSet`, `DiaperChangeViewSet`, `TemperatureViewSet`, `WeightViewSet`, `NoteViewSet`) must filter querysets so a non-staff user can only access records belonging to children they are authorized to view

### Input Validation

- The `FeedingSerializer`, `SleepSerializer`, and `DiaperChangeSerializer` must reject any request body that includes `id`, `is_staff`, `is_superuser`, or `child__slug` in the payload by marking those fields as read-only
- The `Child` name field in `core/models.py` must be validated to reject HTML tags and JavaScript URIs (e.g., `<script>`, `javascript:`) to prevent stored XSS
- Feeding `amount` must be validated as a non-negative decimal; negative values must return HTTP 400

### Security Headers and Cookie Configuration

- `SESSION_COOKIE_SECURE` must default to `True` (not `False`) in `base.py`, overridable only by an explicit environment variable
- `CSRF_COOKIE_SECURE` must default to `True`
- `SECURE_BROWSER_XSS_FILTER` must be set to `True`
- `SECURE_CONTENT_TYPE_NOSNIFF` must be set to `True`
- `X_FRAME_OPTIONS` must be set to `DENY`
- `ALLOWED_HOSTS` must not default to `["*"]`; it must default to an empty list and require explicit configuration

### Middleware Hardening

- `HomeAssistantMiddleware` must validate that the `X-Ingress-Path` header, if present, matches a configured allowlist regex or starts with a known prefix; any non-matching value must be ignored rather than used for URL construction
- `RollingSessionMiddleware` must not extend session expiry for unauthenticated requests

### Expected Functionality

- A regular user accessing `/users/999/password/` (where 999 is another user's PK) receives HTTP 403 Forbidden
- A regular user submitting `{"is_staff": true}` in a PATCH to `/api/feedings/1/` has the field silently ignored
- A POST to `/api/children/` with `<script>alert(1)</script>` as the child's first name returns HTTP 400 with a validation error
- A negative `amount` value in a feeding POST returns HTTP 400
- Response headers include `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`

## Acceptance Criteria

- Non-staff users cannot view, modify, or delete other users' accounts via the user management views — attempts return HTTP 403
- API serializers reject payloads containing privileged fields without applying them to the model
- HTML/script injection in text fields is rejected at the validation layer before database persistence
- All HTTP responses include `X-Content-Type-Options`, `X-Frame-Options`, and `X-XSS-Protection` security headers
- Session and CSRF cookies are marked with the `Secure` flag by default
- The `ALLOWED_HOSTS` setting no longer defaults to a wildcard
- All existing tests in the Baby Buddy test suite continue to pass after the security fixes
