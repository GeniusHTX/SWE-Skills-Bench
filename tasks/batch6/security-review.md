# Task: Perform a Security Review and Fix Vulnerabilities in a Node.js Express API

## Background

A Node.js Express API for a healthcare patient portal has been flagged by an external security audit. The application handles patient records, authentication, file uploads, and payment processing. The codebase contains multiple OWASP Top 10 vulnerabilities that must be identified and fixed: hardcoded secrets, SQL injection, missing input validation, insecure authentication, broken access control, XSS vectors, and insecure file uploads.

## Files to Create/Modify

- `src/config/security.ts` (create) — Security configuration: helmet settings, CORS policy, rate limiting, CSP headers
- `src/middleware/auth.ts` (create) — Secure JWT authentication middleware with httpOnly cookies, token rotation, and refresh tokens
- `src/middleware/validation.ts` (create) — Input validation middleware using Zod schemas for all API endpoints
- `src/middleware/rate-limiter.ts` (create) — Rate limiting middleware with per-endpoint limits (auth=5/min, API=100/min, uploads=10/min)
- `src/middleware/file-upload.ts` (create) — Secure file upload handler with type validation, size limits, filename sanitization, and virus scanning hook
- `src/routes/patients.ts` (create) — Patient CRUD routes with parameterized queries, authorization checks, and audit logging
- `src/routes/auth.ts` (create) — Authentication routes: login, register, refresh, logout with brute-force protection
- `src/utils/crypto.ts` (create) — Cryptographic utilities: password hashing (argon2id), token generation, data encryption at rest (AES-256-GCM)
- `src/utils/sanitize.ts` (create) — Input sanitization: HTML escaping, SQL special character handling, path traversal prevention
- `src/utils/audit-log.ts` (create) — Audit logging for security events: login attempts, data access, privilege changes, failed validations
- `tests/security.test.ts` (create) — Security-focused tests: injection attempts, auth bypass, access control, file upload attacks

## Requirements

### Security Configuration (`src/config/security.ts`)

```typescript
export const securityConfig = {
  helmet: {
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        imgSrc: ["'self'", "data:", "https://cdn.example.com"],
        connectSrc: ["'self'"],
        fontSrc: ["'self'"],
        objectSrc: ["'none'"],
        frameSrc: ["'none'"],
        upgradeInsecureRequests: [],
      },
    },
    hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
    referrerPolicy: { policy: "strict-origin-when-cross-origin" },
    noSniff: true,
    xssFilter: true,
  },
  cors: {
    origin: ["https://portal.example.com"],
    methods: ["GET", "POST", "PUT", "DELETE"],
    allowedHeaders: ["Content-Type", "Authorization"],
    credentials: true,
    maxAge: 600,
  },
  session: {
    cookie: {
      httpOnly: true,
      secure: true,
      sameSite: "strict" as const,
      maxAge: 3600000, // 1 hour
      domain: ".example.com",
    },
  },
};
```

### Authentication (`src/middleware/auth.ts`, `src/routes/auth.ts`)

**Login flow:**
1. Validate email + password input with Zod schema.
2. Query user by email using parameterized query (NOT string concatenation).
3. Verify password using `argon2.verify()` (timing-safe comparison).
4. Generate access token (JWT, 15 min expiry) and refresh token (opaque, 7 day expiry).
5. Store refresh token hash in database (never store plaintext refresh tokens).
6. Set access token in httpOnly, secure, sameSite=strict cookie.
7. Return refresh token in response body (client stores in memory only, NOT localStorage).
8. Log successful login to audit log with IP, user agent, timestamp.

**Failed login:**
1. After 5 failed attempts within 15 minutes: lock account for 30 minutes.
2. Respond with generic `"Invalid email or password"` (never leak whether email exists).
3. Log failed attempt with IP and attempted email to audit log.

**Token refresh:**
1. Accept refresh token in request body.
2. Verify refresh token hash exists in database and is not expired.
3. Rotate: issue new access token + new refresh token, invalidate old refresh token.
4. One-time use: if an already-used refresh token is presented, invalidate ALL tokens for that user (potential token theft detection).

**Logout:**
1. Clear access token cookie.
2. Invalidate refresh token in database.
3. Add current access token JTI to a short-lived blocklist (Redis, TTL = remaining token life).

### Input Validation (`src/middleware/validation.ts`)

Zod schemas for each endpoint:

```typescript
const PatientCreateSchema = z.object({
  firstName: z.string().min(1).max(100).regex(/^[a-zA-Z\s'-]+$/),
  lastName: z.string().min(1).max(100).regex(/^[a-zA-Z\s'-]+$/),
  dateOfBirth: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  email: z.string().email().max(254),
  phone: z.string().regex(/^\+?[1-9]\d{1,14}$/).optional(),
  ssn: z.string().regex(/^\d{3}-\d{2}-\d{4}$/).optional(),
  address: z.object({
    street: z.string().max(200),
    city: z.string().max(100),
    state: z.string().length(2),
    zip: z.string().regex(/^\d{5}(-\d{4})?$/),
  }).optional(),
});

const PatientQuerySchema = z.object({
  page: z.coerce.number().int().min(1).max(1000).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  search: z.string().max(100).optional(),
  sortBy: z.enum(["firstName", "lastName", "dateOfBirth", "createdAt"]).default("createdAt"),
  sortOrder: z.enum(["asc", "desc"]).default("desc"),
});
```

Validation middleware: `validate(schema, source: "body" | "query" | "params")` → returns 400 with structured errors (no stack traces or internal details).

### Patient Routes (`src/routes/patients.ts`)

- **GET `/patients`**: Requires `role: "doctor" | "admin"`. Parameterized query with pagination. Log data access to audit log.
- **GET `/patients/:id`**: Requires `role: "doctor" | "admin"` OR patient accessing own record (`req.user.patientId === req.params.id`). Return 404 (not 403) if patient ID doesn't exist to prevent enumeration.
- **POST `/patients`**: Requires `role: "admin"`. Validate body with `PatientCreateSchema`. Encrypt SSN before storing (AES-256-GCM). Parameterized INSERT query.
- **PUT `/patients/:id`**: Requires `role: "admin"` OR patient updating own record (limited fields: email, phone, address only). Validate body. Audit log the change with before/after values.
- **DELETE `/patients/:id`**: Requires `role: "admin"`. Soft delete only (set `is_active = false`). Audit log.

All queries MUST use parameterized queries:
```typescript
// CORRECT
const result = await db.query('SELECT * FROM patients WHERE id = $1', [patientId]);

// NEVER
const result = await db.query(`SELECT * FROM patients WHERE id = ${patientId}`);
```

### File Upload (`src/middleware/file-upload.ts`)

- Accept only: `image/jpeg`, `image/png`, `application/pdf`.
- Max file size: 10MB.
- Validate MIME type by reading file magic bytes (not trusting `Content-Type` header).
- Sanitize filename: strip path components (`../../etc/passwd` → `etc_passwd`), replace special characters, prepend UUID.
- Store in dedicated uploads directory outside web root (e.g., `/data/uploads/`, not `public/uploads/`).
- Generate signed URL for access (time-limited, 15 minutes).
- Hook for virus scanning: `async scanFile(filePath: string): Promise<boolean>` interface (ClamAV integration point).

### Cryptographic Utilities (`src/utils/crypto.ts`)

- `hashPassword(password: string): Promise<string>`: Argon2id with `memoryCost: 65536`, `timeCost: 3`, `parallelism: 4`.
- `verifyPassword(password: string, hash: string): Promise<boolean>`: Timing-safe verification.
- `generateToken(length: number = 32): string`: Cryptographically random token using `crypto.randomBytes`.
- `encryptPII(plaintext: string, key: Buffer): { ciphertext: string, iv: string, tag: string }`: AES-256-GCM encryption. IV must be unique per encryption (random 12 bytes).
- `decryptPII(encrypted: { ciphertext: string, iv: string, tag: string }, key: Buffer): string`: AES-256-GCM decryption.
- Encryption key loaded from environment variable `ENCRYPTION_KEY` (not hardcoded).

### Audit Logging (`src/utils/audit-log.ts`)

```typescript
interface AuditEvent {
  timestamp: string;      // ISO 8601
  eventType: "auth.login" | "auth.logout" | "auth.failed" | "data.read" | "data.create" | "data.update" | "data.delete" | "upload.success" | "upload.rejected" | "validation.failed";
  userId: string | null;
  ipAddress: string;
  userAgent: string;
  resource: string;       // e.g., "patient:123"
  details: Record<string, unknown>;
  outcome: "success" | "failure";
}
```

- Write to structured JSON log file (one event per line) AND database table for queryability.
- Never log sensitive data: no passwords, tokens, SSNs, or full request bodies.
- Mask PII in logs: email → `j***@example.com`, phone → `***-***-1234`.

### Security Tests (`tests/security.test.ts`)

- **SQL Injection**: Send `'; DROP TABLE patients; --` in search query parameter → returns 400 validation error, database unchanged.
- **XSS**: Send `<script>alert('xss')</script>` in patient firstName → returns 400 (fails regex validation).
- **Path Traversal**: Upload file named `../../../etc/passwd` → filename sanitized, stored safely.
- **Auth Bypass**: Request `/patients` without token → 401. Request with expired token → 401. Request with tampered token → 401.
- **Broken Access Control**: Patient with `patientId: 1` requests `/patients/2` → 404!. Doctor requests `/patients/2` → 200.
- **Brute Force**: Send 6 failed login attempts → 6th returns 429 with lockout message.
- **Token Reuse**: Use refresh token twice → second attempt invalidates all user tokens.
- **File Type Bypass**: Upload `.exe` file with `Content-Type: image/jpeg` → rejected by magic byte check.
- **Rate Limiting**: Send 101 requests in 1 minute to API endpoint → 101st returns 429.

### Expected Functionality

- Login returns httpOnly cookie with JWT, NOT in response body.
- Patient SSN encrypted at rest with AES-256-GCM, decrypted only for authorized viewers.
- All database queries use parameterized statements; no string interpolation.
- Upload of malicious file rejected; legitimate PDF/image stored with sanitized name.
- Audit log records all authentication events and data access with masked PII.
- After 5 failed logins, account locked for 30 minutes.

## Acceptance Criteria

- Security config sets CSP headers blocking inline scripts, HSTS with 1-year max-age and preload, CORS restricted to portal domain.
- Authentication uses argon2id for password hashing with recommended parameters (memoryCost 65536, timeCost 3).
- JWT access tokens stored in httpOnly/secure/sameSite=strict cookies (not localStorage).
- Refresh token rotation: new refresh token issued on each refresh, old token invalidated. Reuse detection invalidates all user tokens.
- Account lockout after 5 failed attempts within 15 minutes, 30-minute lockout duration.
- All input validated with Zod schemas before processing. Validation errors return 400 with no internal details.
- Patient queries use parameterized SQL (`$1` placeholders), never string concatenation.
- Access control: patients can only access own records; non-existent resources return 404 (not 403) to prevent enumeration.
- File uploads validated by magic bytes (not Content-Type header), filenames sanitized to prevent path traversal.
- PII (SSN) encrypted at rest with AES-256-GCM using environment-sourced key and unique IV per encryption.
- Audit log records all security events with masked PII, structured JSON format, both file and database storage.
- Rate limiter applies per-endpoint limits: 5/min for auth, 100/min for API, 10/min for uploads.
- Security tests verify SQL injection, XSS, path traversal, auth bypass, access control, brute force, token reuse, and file type bypass are all blocked.
