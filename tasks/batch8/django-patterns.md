# Task: Implement a Wishlist Feature with REST API in Saleor

## Background

Saleor (https://github.com/saleor/saleor) is an open-source, GraphQL-first e-commerce platform built with Django and Django REST Framework. The platform currently supports products, orders, carts, and user accounts, but lacks a wishlist feature. Authenticated users should be able to save products to a personal wishlist, view their list, remove items, and move items to the cart. The feature must follow Saleor's existing architecture patterns including its app structure, model conventions, and API style.

## Files to Create/Modify

- `saleor/wishlist/models.py` (create) — `Wishlist` and `WishlistItem` Django models with user association, product variant references, and timestamps
- `saleor/wishlist/migrations/0001_initial.py` (create) — Initial migration for wishlist tables
- `saleor/wishlist/views.py` (create) — DRF ViewSet with list, create, retrieve, destroy, and `move_to_cart` custom action
- `saleor/wishlist/serializers.py` (create) — DRF serializers for wishlist items with nested product representation and input validation
- `saleor/wishlist/urls.py` (create) — URL configuration for wishlist API endpoints
- `saleor/wishlist/__init__.py` (create) — Package init
- `saleor/core/urls.py` (modify) — Register wishlist URLs under `/api/wishlist/`
- `saleor/wishlist/tests/test_models.py` (create) — Model-level tests for constraints and relationships
- `saleor/wishlist/tests/test_views.py` (create) — API tests covering CRUD, authorization, and edge cases

## Requirements

### Wishlist Model

- `Wishlist` model with fields: `id` (UUID, primary key), `user` (OneToOneField to the User model), `created_at` (auto-set DateTimeField)
- `WishlistItem` model with fields: `id` (UUID, primary key), `wishlist` (ForeignKey to `Wishlist`), `product_variant` (ForeignKey to `ProductVariant`), `added_at` (auto-set DateTimeField), `note` (CharField, max 200 characters, optional)
- A unique constraint on `(wishlist, product_variant)` to prevent duplicate items
- Deleting a `ProductVariant` must cascade to remove associated `WishlistItem` entries
- Deleting a `User` must cascade to remove their `Wishlist` and all items

### REST API Endpoints

- `GET /api/wishlist/` — List the authenticated user's wishlist items, paginated (20 items per page), ordered by `added_at` descending; each item includes product variant details (name, price, image URL, availability status)
- `POST /api/wishlist/` — Add a product variant to the wishlist; request body: `{"variant_id": "<uuid>", "note": "optional note"}`; returns HTTP 201 on success, HTTP 409 if the variant is already in the wishlist, HTTP 404 if the variant does not exist
- `GET /api/wishlist/{item_id}/` — Retrieve a single wishlist item; HTTP 200 or HTTP 404
- `DELETE /api/wishlist/{item_id}/` — Remove an item from the wishlist; HTTP 204 or HTTP 404
- `PATCH /api/wishlist/{item_id}/` — Update the `note` field; HTTP 200 or HTTP 404
- `POST /api/wishlist/{item_id}/move_to_cart/` — Remove the item from the wishlist and add the variant to the user's active checkout/cart; returns HTTP 200 with the created cart line, or HTTP 400 if the variant is out of stock

### Authorization

- All endpoints require authentication; unauthenticated requests must receive HTTP 401
- Users can only access their own wishlist; requesting another user's wishlist item returns HTTP 404 (not 403, to avoid leaking existence)
- The queryset must be scoped to the authenticated user in the ViewSet's `get_queryset()` method

### Serializer Validation

- `variant_id` must reference an existing, active `ProductVariant`; inactive or deleted variants must be rejected with HTTP 400 and a message `"Product variant not found or inactive"`
- `note` must not exceed 200 characters; longer values must be rejected with HTTP 400
- The response serializer must include nested read-only fields: `variant_name`, `variant_price` (as decimal string), `product_name`, `is_available` (boolean based on stock)

### Move to Cart Logic

- `move_to_cart` must check that the product variant is in stock (quantity > 0); if not, return HTTP 400 with message `"Variant is out of stock"`
- If the user has no active checkout, one must be created
- If the variant already exists in the cart, its quantity must be incremented by 1 (not duplicated)
- The wishlist item must be deleted only after the cart line is successfully created or updated

## Expected Functionality

- An authenticated user can `POST /api/wishlist/` with `{"variant_id": "abc-123"}` and receive HTTP 201 with the created wishlist item
- Posting the same `variant_id` again returns HTTP 409
- `GET /api/wishlist/` returns a paginated list showing product name, price, availability for each item
- `POST /api/wishlist/{id}/move_to_cart/` for an in-stock variant removes it from the wishlist and adds it to the cart
- `POST /api/wishlist/{id}/move_to_cart/` for an out-of-stock variant returns HTTP 400 and does not remove the item from the wishlist
- An unauthenticated request to any wishlist endpoint returns HTTP 401

## Acceptance Criteria

- `Wishlist` and `WishlistItem` models are created with proper relationships, unique constraints, and cascade deletes
- CRUD endpoints for wishlist items work correctly with proper HTTP status codes (201, 200, 204, 400, 401, 404, 409)
- All endpoints enforce authentication and scope data to the authenticated user only
- The `move_to_cart` action checks stock availability, creates or updates the cart line, and removes the wishlist item atomically
- Duplicate variant additions are rejected with HTTP 409
- Inactive or nonexistent product variants are rejected during creation
- Response payloads include nested product variant details (name, price, availability)
- All tests pass with `pytest`
