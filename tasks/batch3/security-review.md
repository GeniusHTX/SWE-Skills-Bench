# Task: Implement Security Hardening for Baby Buddy's User Input and Authentication

## Background

Baby Buddy (https://github.com/babybuddy/babybuddy) is a Django-based child care tracking application. A security review has identified several areas requiring hardening: user input validation on API endpoints, protection against common injection attacks, authentication improvements, and secrets management. This task implements the identified security fixes.

## Files to Create/Modify

- `babybuddy/middleware/security.py` (create) — Security middleware: rate limiting, request validation, security headers
- `api/validators.py` (create) — Input validation and sanitization for API endpoints
- `babybuddy/auth_hardening.py` (create) — Authentication hardening: password policy, account lockout, session management
- `tests/test_security.py` (create) — Security-focused tests covering injection, authentication, and header validation

## Requirements

### Input Validation and Sanitization

- Implement an `InputValidator` class for API request payloads with the following rules:
  - String fields: strip leading/trailing whitespace, reject strings containing `<script`, `javascript:`, `on\w+=` (XSS patterns); raise `ValidationError` with field name and rejection reason
  - Numeric fields: validate type and range; reject NaN and Infinity values
  - Date/time fields: validate ISO 8601 format; reject dates more than 1 year in the future or before year 2000
  - All fields: reject null bytes (`\x00`) in any string input
- Apply validation to the Baby Buddy API endpoints for creating and updating child records, feeding entries, and diaper change entries
- The validator must sanitize HTML entities in text fields (convert `<` to `&lt;`, `>` to `&gt;`, `&` to `&amp;`, `"` to `&quot;`)

### SQL Injection Prevention

- Audit and fix any raw SQL queries in the codebase to use parameterized queries
- Implement a `SafeQueryBuilder` class that constructs Django ORM queries from user-provided filter parameters
- The `SafeQueryBuilder` accepts a whitelist of allowed filter fields and operators (`exact`, `contains`, `gt`, `lt`, `gte`, `lte`); reject any field or operator not in the whitelist with a `SecurityError`
- Log rejected query attempts at WARNING level with the attempted field/operator (but not the user-provided value, to avoid log injection)

### Authentication Hardening

- Implement a password policy: minimum 10 characters, at least one uppercase letter, one lowercase letter, one digit, and one special character; raise `PasswordPolicyError` with specific failures listed
- Implement account lockout: after 5 consecutive failed login attempts, lock the account for 15 minutes; provide `check_lockout(username) -> bool` and `record_failed_attempt(username)` functions
- The lockout counter resets after a successful login
- Implement session timeout: sessions expire after 30 minutes of inactivity (configurable)
- Session tokens must be regenerated after authentication (to prevent session fixation)

### Security Headers Middleware

- Implement Django middleware that adds the following response headers:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (only when `settings.SECURE_SSL_REDIRECT` is True)
  - `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'`
  - `Referrer-Policy: strict-origin-when-cross-origin`
- Headers must not duplicate existing headers set by other middleware

### Expected Functionality

- A child name containing `<script>alert('xss')</script>` is rejected with `ValidationError` mentioning the XSS pattern
- A feeding amount of `NaN` is rejected with `ValidationError`
- A filter request for field `password__regex` is rejected by `SafeQueryBuilder` (not in whitelist)
- 5 failed login attempts for user "admin" result in a lockout; the 6th attempt is rejected even with the correct password
- After 15 minutes, the locked-out user can log in again
- A password "short" raises `PasswordPolicyError` listing all unmet requirements
- All security headers are present in HTTP responses

## Acceptance Criteria

- `InputValidator` rejects XSS patterns, null bytes, NaN/Infinity values, and out-of-range dates with specific error messages
- HTML entities are properly sanitized in text fields
- `SafeQueryBuilder` rejects any field or operator not in the whitelist and logs the attempt
- Password policy enforces all specified requirements and lists all violations
- Account lockout activates after 5 failures, lasts 15 minutes, and resets on successful login
- Session timeout and regeneration are implemented correctly
- All 6 security headers are present in responses, with HSTS conditional on SSL configuration
- Tests cover XSS injection attempts, SQL injection attempts, account lockout lifecycle, password policy edge cases, and header verification
