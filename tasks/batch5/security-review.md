# Task: Harden Authentication and Input Validation in Baby Buddy

## Background

Baby Buddy (https://github.com/babybuddy/babybuddy) is a Django-based child-tracking application. The API and web views handle sensitive data (child health records, caregiver information). Several endpoints currently lack sufficient input validation, and the authentication configuration has gaps that could expose data to unauthorized users. This task focuses on hardening specific views and API endpoints against common web security vulnerabilities.

## Files to Create/Modify

- `babybuddy/settings/base.py` (modify) — Tighten session cookie settings, CSRF configuration, and security-related middleware defaults.
- `api/serializers.py` (modify) — Add strict input validation to the `ChildSerializer`, `FeedingSerializer`, `SleepSerializer`, and `TimerSerializer` fields.
- `api/views.py` (modify) — Enforce object-level permission checks so users can only access children and records they are authorized to see.
- `api/filters.py` (modify) — Sanitize filter query parameters to prevent injection through ORM filter expressions.
- `core/templates/core/child_detail.html` (modify) — Ensure all user-supplied data rendered in the template is properly escaped.
- `babybuddy/middleware.py` (create or modify) — Add rate limiting for authentication endpoints and enforce security headers.

## Requirements

### Session and Cookie Security

- Session cookies must be `HttpOnly`, `Secure` (when `HTTPS=true`), and have `SameSite=Lax` or `Strict`.
- CSRF cookies must also be `Secure` when HTTPS is enabled.
- Session timeout must be set to a maximum of 12 hours of inactivity.

### API Input Validation

- `ChildSerializer`: `first_name` and `last_name` must be non-empty, max 255 characters, and must not contain HTML tags or script content.
- `FeedingSerializer`: `amount` must be a positive decimal ≤ 1000; `type` must be one of the defined choices (`breast milk`, `formula`, `fortified breast milk`, `solid food`); `start` must be earlier than `end`.
- `SleepSerializer`: `start` must be earlier than `end`; duration must not exceed 24 hours.
- `TimerSerializer`: `name` max 255 characters; `start` cannot be in the future.

### Object-Level Permissions

- API views must filter query sets so authenticated users only see children and related records they have permission to access.
- Attempting to read or modify another user's child record via direct ID access must return 403 Forbidden (not 404).
- Unauthenticated requests to any API endpoint must return 401 Unauthorized.

### Template Output Encoding

- All dynamic content in `child_detail.html` must be rendered using Django's auto-escaping; any `|safe` filter usage on user-supplied data must be removed.
- Child names, notes, and custom fields must not be rendered as raw HTML.

### Expected Functionality

- `POST /api/feedings/` with `amount: -5` → 400 Bad Request with validation error.
- `POST /api/feedings/` with `start` later than `end` → 400 Bad Request.
- `GET /api/children/` as user A → returns only user A's children, not user B's.
- `GET /api/children/{user_b_child_id}/` as user A → 403 Forbidden.
- A child named `<script>alert(1)</script>` is displayed as escaped text in the detail template, not executed.
- Unauthenticated `GET /api/children/` → 401 Unauthorized.

## Acceptance Criteria

- Session cookies include `HttpOnly`, `Secure` (when HTTPS is on), and `SameSite` attributes.
- API serializers reject invalid inputs (negative amounts, illogical time ranges, oversized strings, HTML in name fields) with 400-level responses.
- Object-level permissions prevent users from accessing children or records they do not own, returning 403 for unauthorized direct-ID access.
- All user-supplied text in `child_detail.html` is HTML-escaped in the rendered output.
- Unauthenticated API requests receive 401 responses.
- The application starts and serves requests without errors after all changes.
