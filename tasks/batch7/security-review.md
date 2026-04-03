# Task: Harden Authentication and Input Validation in Baby Buddy

## Background

Baby Buddy (https://github.com/babybuddy/babybuddy) is a Django-based application that helps caregivers track sleep, feedings, diaper changes, and other infant-care activities. The application exposes a REST API under `api/` and web views under `core/` and `babybuddy/`. Several areas of the codebase need security hardening: the API lacks consistent rate limiting and input sanitization, session configuration does not follow current best practices, and certain views accept user-supplied data without adequate validation.

## Files to Create/Modify

- `babybuddy/settings/base.py` (modify) — Tighten session cookie flags, add security middleware settings, and configure CSRF protections
- `api/views.py` (modify) — Add input length validation and sanitization for API endpoints that accept free-text fields (notes, names)
- `api/serializers.py` (modify) — Add field-level validation for serializer fields that accept user input
- `core/views.py` (modify) — Add server-side validation for form submissions that create or update Child, Feeding, Sleep, DiaperChange, and TummyTime records
- `core/forms.py` (modify) — Add input validation constraints for date/time ranges, text length limits, and enumerated-value checks
- `babybuddy/middleware.py` (create) — Implement rate-limiting middleware for authentication endpoints (`/login/`, `/api/` token endpoints)

## Requirements

### Session and Cookie Security

- The `SESSION_COOKIE_SECURE` setting must be set to `True` in production configurations
- The `SESSION_COOKIE_HTTPONLY` setting must be `True`
- The `SESSION_COOKIE_SAMESITE` setting must be `"Lax"` or `"Strict"`
- The `CSRF_COOKIE_HTTPONLY` setting must be `True`
- The `SESSION_COOKIE_AGE` must not exceed 1209600 seconds (14 days)
- The `SECURE_BROWSER_XSS_FILTER` setting must be enabled
- The `X_FRAME_OPTIONS` setting must be `"DENY"` or `"SAMEORIGIN"`

### Input Validation — API

- All free-text fields (`notes` on Feeding, Sleep, DiaperChange, TummyTime; `first_name`/`last_name` on Child) must enforce a maximum length of 1000 characters at the serializer level
- Date and time fields must reject values in the future beyond a reasonable tolerance (no more than 24 hours ahead of server time)
- The `start` time of a timed entry must be before its `end` time; API requests violating this must return HTTP 400 with a descriptive error message
- Enumerated fields (`method` on Feeding: breast milk, formula, fortified breast milk, solid food; `color` on DiaperChange: black, brown, green, yellow) must reject unknown values with HTTP 400

### Input Validation — Web Forms

- All form text inputs must strip leading/trailing whitespace before saving
- Child name fields must reject strings that are empty after stripping
- The core forms for Feeding, Sleep, DiaperChange, and TummyTime must validate that `start` < `end` and display a form error if violated
- Numeric fields (e.g., `amount` on Feeding) must reject negative values

### Rate Limiting

- The login endpoint (`/login/`) must be rate-limited to 10 attempts per IP per minute
- After the rate limit is exceeded, subsequent requests must receive HTTP 429 with a `Retry-After` header
- The API token authentication endpoint must be rate-limited to 5 attempts per IP per minute
- Rate-limit state may be stored in Django's cache framework

### No Regressions

- Existing authentication flows (login, logout, API token auth) must continue to work for legitimate users
- Existing API consumers that send valid data must receive the same response codes and data shapes as before
- All existing tests in the project must continue to pass

## Expected Functionality

- A POST to `/api/feedings/` with `notes` exceeding 1000 characters → HTTP 400 with a validation error on the `notes` field
- A POST to `/api/sleep/` with `start` after `end` → HTTP 400 with an error message about invalid time range
- A POST to `/api/changes/` with `color` set to `"purple"` → HTTP 400 with an error about invalid choice
- Submitting the web Feeding form with a negative `amount` → form re-renders with an error message
- 11 rapid POST requests to `/login/` from the same IP within 60 seconds → the 11th request receives HTTP 429
- A normal user login with correct credentials → HTTP 302 redirect to dashboard (unchanged behavior)

## Acceptance Criteria

- Session and CSRF cookie settings conform to the specified secure values
- All API serializer text fields enforce a maximum length of 1000 characters
- API endpoints reject future-dated entries, inverted time ranges, and invalid enumerated values with HTTP 400
- Web form submissions validate text length, date ordering, and numeric constraints before saving
- The login and API token endpoints enforce per-IP rate limits and return HTTP 429 with `Retry-After` when exceeded
- Existing application functionality (CRUD for all models, authentication, API responses) is unaffected for valid inputs
