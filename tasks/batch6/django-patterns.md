# Task: Add Wishlist Feature with GraphQL API to Saleor

## Background

The Saleor e-commerce platform (https://github.com/saleor/saleor) needs a wishlist feature that allows authenticated customers to save products they are interested in purchasing later. The feature requires a new Django model, GraphQL mutations and queries, a service layer for business logic, and integration with Saleor's existing permission and caching systems.

## Files to Create/Modify

- `saleor/wishlist/models.py` (create) — Wishlist and WishlistItem Django models with proper relationships to User and Product
- `saleor/wishlist/__init__.py` (create) — Module initialization
- `saleor/wishlist/migrations/0001_initial.py` (create) — Database migration for wishlist tables
- `saleor/graphql/wishlist/schema.py` (create) — GraphQL types, queries, and mutations for wishlist operations
- `saleor/graphql/wishlist/mutations.py` (create) — GraphQL mutations: WishlistAddProduct, WishlistRemoveProduct, WishlistClear
- `saleor/graphql/wishlist/types.py` (create) — GraphQL object types: WishlistType, WishlistItemType
- `saleor/graphql/wishlist/resolvers.py` (create) — Query resolvers for fetching wishlist data with optimized queries
- `saleor/graphql/schema.py` (modify) — Register wishlist queries and mutations in the root schema
- `saleor/core/permissions.py` (modify) — Add wishlist-related permissions if needed
- `saleor/wishlist/tests/test_wishlist_models.py` (create) — Model unit tests
- `saleor/wishlist/tests/test_wishlist_api.py` (create) — GraphQL API integration tests

## Requirements

### Data Model

- `Wishlist` model:
  - `id` — UUID primary key (consistent with Saleor's existing convention).
  - `user` — ForeignKey to Saleor's User model, `on_delete=CASCADE`, with `related_name="wishlists"`. Each user should have at most one default wishlist.
  - `name` — CharField, max_length=250, default `"Default"`.
  - `created_at` — DateTimeField, auto_now_add.
  - Unique constraint on `(user, name)` — a user cannot have two wishlists with the same name.

- `WishlistItem` model:
  - `id` — UUID primary key.
  - `wishlist` — ForeignKey to Wishlist, `on_delete=CASCADE`, `related_name="items"`.
  - `product` — ForeignKey to Saleor's Product model, `on_delete=CASCADE`.
  - `added_at` — DateTimeField, auto_now_add.
  - Unique constraint on `(wishlist, product)` — the same product cannot appear twice in one wishlist.
  - `Meta.ordering = ["-added_at"]`.

### GraphQL Queries

- `wishlist` — returns the authenticated user's default wishlist with its items.
  - Must prefetch related product data to avoid N+1 queries.
  - Returns `null` if the user has no wishlist yet.
  - Anonymous users receive a `PermissionDenied` error.

- `wishlistItems(first: Int, after: String)` — paginated list of items in the user's wishlist using Relay-style cursor pagination.

### GraphQL Mutations

- `wishlistAddProduct(productId: ID!)`:
  - Adds a product to the user's default wishlist. Creates the wishlist if it doesn't exist.
  - If the product is already in the wishlist, return the existing wishlist without error (idempotent).
  - If the `productId` does not refer to an existing, published product, return an error with code `NOT_FOUND` and message `"Product not found."`.
  - Returns the updated `Wishlist` object.

- `wishlistRemoveProduct(productId: ID!)`:
  - Removes a product from the user's default wishlist.
  - If the product is not in the wishlist, return the wishlist without error (idempotent).
  - Returns the updated `Wishlist` object.

- `wishlistClear`:
  - Removes all items from the user's default wishlist without deleting the wishlist itself.
  - Returns the empty `Wishlist` object.

- All mutations require authentication. Anonymous callers receive `PermissionDenied`.

### Business Rules

- A wishlist can hold a maximum of 200 items. Attempting to add beyond this limit returns an error with code `LIMIT_EXCEEDED` and message `"Wishlist cannot contain more than 200 items."`.
- Only published products (where `product.is_published` is True) can be added to a wishlist.
- When a product is deleted from the system, its corresponding WishlistItem entries are automatically removed (CASCADE).

### Expected Functionality

- Authenticated user calls `wishlistAddProduct(productId: "UHJvZHVjdDox")` → product is added, response includes updated wishlist with the new item.
- Same call repeated → same response, no duplicate item created.
- `wishlistAddProduct` with a non-existent product ID → error response with `NOT_FOUND`.
- `wishlistRemoveProduct(productId: "UHJvZHVjdDox")` → product removed, response includes updated wishlist.
- `wishlistClear` → all items removed, response shows wishlist with empty items list.
- `wishlist` query → returns the wishlist with all items and their product details in a single optimized query.
- Adding the 201st item → error with `LIMIT_EXCEEDED`.

## Acceptance Criteria

- Django models `Wishlist` and `WishlistItem` are created with proper foreign keys, unique constraints, and UUID primary keys.
- Database migration is generated and applies cleanly.
- GraphQL queries `wishlist` and `wishlistItems` return correct data with optimized prefetching.
- GraphQL mutations `wishlistAddProduct`, `wishlistRemoveProduct`, and `wishlistClear` modify the wishlist correctly.
- Adding a product that already exists in the wishlist is idempotent and does not raise an error.
- The 200-item limit is enforced with a descriptive error message.
- Only published products can be added; unpublished or non-existent products are rejected.
- All mutations and queries require authentication; anonymous access returns permission errors.
- Wishlist items are automatically cleaned up when the referenced product is deleted.
