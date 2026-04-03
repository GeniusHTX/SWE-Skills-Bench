# Task: Implement a URL Shortener Service Using Test-Driven Development

## Background

A URL shortener service needs to be built following strict TDD methodology: write failing tests first, then implement minimal code to pass, then refactor. The service exposes a REST API for creating short URLs, redirecting, tracking click analytics, and managing link expiration. The tech stack is TypeScript with Express and PostgreSQL, using Vitest for testing and Playwright for E2E tests.

## Files to Create/Modify

- `src/services/url-shortener.ts` (create) — Core business logic: generate short codes, validate URLs, manage expiration
- `src/services/analytics.ts` (create) — Click tracking: record clicks with metadata, aggregate statistics
- `src/routes/api.ts` (create) — Express routes: POST /api/shorten, GET /:code, GET /api/stats/:code, DELETE /api/links/:code
- `src/db/repository.ts` (create) — Database access: CRUD operations for short links and click events
- `src/db/migrations/001_create_tables.sql` (create) — PostgreSQL schema: short_links and click_events tables
- `tests/unit/url-shortener.test.ts` (create) — Unit tests for URL shortener service
- `tests/unit/analytics.test.ts` (create) — Unit tests for analytics service
- `tests/integration/api.test.ts` (create) — Integration tests for all API endpoints
- `tests/e2e/redirect.spec.ts` (create) — Playwright E2E test for redirect flow

## Requirements

### Database Schema (`src/db/migrations/001_create_tables.sql`)

- `short_links` table:
  - `id` — serial primary key
  - `code` — varchar(10), unique, not null, indexed
  - `original_url` — text, not null
  - `created_at` — timestamp with time zone, default now()
  - `expires_at` — timestamp with time zone, nullable
  - `click_count` — integer, default 0
  - `is_active` — boolean, default true
  - `created_by_ip` — inet, nullable

- `click_events` table:
  - `id` — serial primary key
  - `link_id` — integer, foreign key → short_links(id) on delete cascade
  - `clicked_at` — timestamp with time zone, default now()
  - `ip_address` — inet, nullable
  - `user_agent` — text, nullable
  - `referer` — text, nullable
  - `country` — varchar(2), nullable

### Unit Tests — URL Shortener (`tests/unit/url-shortener.test.ts`)

Write these tests FIRST (they must fail before implementation):

```
describe('URLShortener', () => {
  describe('generateCode', () => {
    it('generates a code of exactly 7 characters')
    it('generates unique codes for consecutive calls')
    it('generates codes using only alphanumeric characters [a-zA-Z0-9]')
    it('accepts custom code length between 4 and 10')
    it('throws error for code length outside 4-10 range')
  })

  describe('validateUrl', () => {
    it('accepts valid HTTP URLs')
    it('accepts valid HTTPS URLs')
    it('rejects URLs without protocol')
    it('rejects non-HTTP protocols (ftp://, javascript:)')
    it('rejects URLs with localhost or 127.0.0.1')
    it('rejects URLs with private IP ranges (10.x, 172.16-31.x, 192.168.x)')
    it('accepts URLs with ports')
    it('rejects URLs exceeding 2048 characters')
  })

  describe('createShortLink', () => {
    it('creates a short link and returns code + shortened URL')
    it('sets expiration when ttl_hours is provided')
    it('rejects duplicate custom codes with ConflictError')
    it('retries code generation on collision up to 3 times')
  })

  describe('resolveCode', () => {
    it('returns original URL for valid active code')
    it('throws NotFoundError for non-existent code')
    it('throws ExpiredError for expired links')
    it('throws InactiveError for deactivated links')
  })
})
```

### Unit Tests — Analytics (`tests/unit/analytics.test.ts`)

```
describe('AnalyticsService', () => {
  describe('recordClick', () => {
    it('creates a click event with IP, user agent, and referer')
    it('increments the link click_count')
    it('does not record click for expired links')
  })

  describe('getStats', () => {
    it('returns total clicks, unique IPs, and clicks per day for a code')
    it('returns empty stats for code with no clicks')
    it('filters stats by date range when start/end provided')
    it('returns top 5 referers sorted by count')
    it('returns top 5 countries sorted by count')
  })
})
```

### Integration Tests (`tests/integration/api.test.ts`)

- `POST /api/shorten` with `{ "url": "https://example.com" }` → 201, body contains `{ "code": "...", "short_url": "http://localhost:3000/..." }`.
- `POST /api/shorten` with `{ "url": "https://example.com", "custom_code": "mylink", "ttl_hours": 24 }` → 201, code is `"mylink"`.
- `POST /api/shorten` with `{ "url": "not-a-url" }` → 400, body contains `{ "error": "Invalid URL" }`.
- `POST /api/shorten` with `{ "url": "http://192.168.1.1/admin" }` → 400, body contains `{ "error": "Private URLs are not allowed" }`.
- `GET /:code` with valid code → 302 redirect to original URL.
- `GET /:code` with expired code → 410 Gone.
- `GET /:code` with non-existent code → 404 Not Found.
- `GET /api/stats/:code` → 200, body contains `{ "total_clicks": int, "unique_visitors": int, "clicks_per_day": [...], "top_referers": [...] }`.
- `DELETE /api/links/:code` → 204 No Content, subsequent GET → 404.

### E2E Test (`tests/e2e/redirect.spec.ts`)

- Navigate to the app, create a short URL via the API, navigate to the short URL, assert the browser is redirected to the original URL.
- Create a short URL with `ttl_hours: 0` (immediate expiry), navigate to it, assert 410 response.

### Implementation (`src/services/url-shortener.ts`)

After tests are written:
- `generateCode(length: number = 7): string` — cryptographically random alphanumeric code using `crypto.randomBytes`.
- `validateUrl(url: string): { valid: boolean, error?: string }` — parse with `URL` constructor, check protocol, check for private IPs/localhost.
- `createShortLink(url: string, options?: { custom_code?: string, ttl_hours?: number, client_ip?: string }): Promise<ShortLink>`.
- `resolveCode(code: string): Promise<string>` — returns original URL or throws typed error.

### Expected Functionality

- TDD cycle: all tests fail initially → implement code → all tests pass → refactor.
- `POST /api/shorten { "url": "https://github.com" }` → `{ "code": "aB3kL9x", "short_url": "http://localhost:3000/aB3kL9x" }`.
- `GET /aB3kL9x` → 302 redirect to `https://github.com`, click recorded.
- `GET /api/stats/aB3kL9x` after 3 clicks → `{ "total_clicks": 3, "unique_visitors": 2, ... }`.
- Test coverage ≥ 80% across unit + integration tests.

## Acceptance Criteria

- All unit tests are written before their corresponding implementation code and fail when run against empty stubs.
- Unit tests cover: code generation (length, uniqueness, character set), URL validation (protocol, private IPs, length), link creation, resolution, expiration.
- Analytics tests cover: click recording, click counting, stats aggregation with date range filtering, top referers/countries.
- Integration tests verify all 4 API endpoints with success and error cases including 400, 404, 410 responses.
- E2E test confirms browser redirect from short URL to original URL.
- URL validation rejects private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) and localhost.
- Short codes are cryptographically random, 7 characters by default, alphanumeric only.
- Expired links return 410 Gone, not 404.
- Test coverage is at least 80% across the codebase.
