# Task: Add a Product Gift Card API Resource to Saleor

## Background

Saleor (https://github.com/saleor/saleor) is a GraphQL-first e-commerce platform built on Django and Django REST Framework. The platform already supports products, orders, and vouchers. A new "Gift Card Template" management feature is needed, allowing staff to create, list, update, and deactivate reusable gift card templates with customizable denominations and expiration policies through the REST API.

## Files to Create/Modify

- `saleor/giftcard/models.py` (modify) — Add a `GiftCardTemplate` model representing a reusable template with fields for name, fixed denominations, expiration policy, and active status.
- `saleor/giftcard/serializers.py` (create) — DRF serializers for `GiftCardTemplate`: a list serializer (summary fields) and a detail serializer (full fields including nested denominations).
- `saleor/giftcard/views.py` (create) — DRF ViewSet for `GiftCardTemplate` with `list`, `retrieve`, `create`, `update`, and a custom `deactivate` action.
- `saleor/giftcard/urls.py` (create) — URL routing for the gift card template ViewSet, registered under `/api/gift-card-templates/`.
- `saleor/giftcard/permissions.py` (create) — Custom permission class restricting write operations to staff users with the `manage_gift_cards` permission.
- `saleor/giftcard/tests/test_gift_card_template_api.py` (create) — Tests covering CRUD operations, permission enforcement, validation errors, and pagination.

## Requirements

### GiftCardTemplate Model

- `name`: string, required, max 255 characters, unique.
- `denominations`: JSON field storing a list of decimal amounts (e.g., `[25.00, 50.00, 100.00]`); at least one denomination required.
- `currency`: string (ISO 4217 code), required, max 3 characters.
- `expiration_days`: positive integer or `null` (null means no expiration).
- `is_active`: boolean, default `True`.
- `created_at`, `updated_at`: auto-managed datetime fields.

### API Endpoints

- `GET /api/gift-card-templates/` — Paginated list of templates; support `?is_active=true` and `?currency=USD` filters.
- `GET /api/gift-card-templates/{id}/` — Full detail of a single template.
- `POST /api/gift-card-templates/` — Create a new template; validate required fields and denomination constraints.
- `PUT /api/gift-card-templates/{id}/` — Update name, denominations, currency, or expiration_days.
- `POST /api/gift-card-templates/{id}/deactivate/` — Set `is_active=False`; deactivating an already-inactive template returns 400.

### Validation Rules

- `denominations` must be a non-empty list of positive decimals; values ≤ 0 or non-numeric entries are rejected.
- `currency` must be a valid 3-letter ISO 4217 code (validate against a known list).
- `expiration_days` if provided must be > 0.
- Duplicate `name` on creation or update returns 400 with a descriptive message.

### Permissions

- Anonymous users receive 401 for all endpoints.
- Authenticated users without `manage_gift_cards` permission receive 403 for write operations but can read (list/retrieve).
- Staff users with `manage_gift_cards` permission can perform all operations.

### Expected Functionality

- `POST /api/gift-card-templates/` with `{"name": "Holiday Card", "denominations": [25, 50, 100], "currency": "USD"}` → 201 with the created template.
- `GET /api/gift-card-templates/?is_active=true&currency=USD` → paginated list of active USD templates.
- `POST /api/gift-card-templates/` with `{"name": "Bad", "denominations": [-10], "currency": "USD"}` → 400 validation error for negative denomination.
- `POST /api/gift-card-templates/{id}/deactivate/` on active template → 200 with `is_active: false`.
- `POST /api/gift-card-templates/{id}/deactivate/` on already-inactive template → 400 error.

## Acceptance Criteria

- The `GiftCardTemplate` model is defined with all required fields and constraints.
- All five API endpoints respond with correct HTTP status codes and response bodies.
- Validation rejects invalid denominations, bad currency codes, and duplicate names with 400 responses.
- Permission checks enforce 401 for unauthenticated and 403 for unauthorized write operations.
- The `deactivate` action sets `is_active=False` and rejects re-deactivation.
- Tests cover CRUD, permission enforcement, each validation rule, and the deactivation edge case.
