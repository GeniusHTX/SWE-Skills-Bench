# Task: Add a Product Review System to Saleor E-Commerce

## Background

The Saleor e-commerce platform (Django/GraphQL backend) needs a product review system that allows authenticated customers to submit, update, and query reviews for products. Reviews include a star rating, text body, and moderation status. The implementation must follow Saleor's existing architecture: Django models with proper indexing, a service layer for business logic, GraphQL mutations and queries exposed via the `saleor/graphql/` schema, and full test coverage.

## Files to Create/Modify

- `saleor/product/models.py` (modify) — Add `ProductReview` model with fields, indexes, constraints, and a custom QuerySet
- `saleor/product/migrations/0XXX_add_product_review.py` (create) — Django migration for the new model
- `saleor/product/services.py` (create) — Service layer encapsulating review creation, update, moderation, and aggregation logic
- `saleor/graphql/product/types.py` (modify) — Add `ProductReviewType` GraphQL type and connect it to the `Product` type as a `reviews` field
- `saleor/graphql/product/mutations.py` (modify) — Add `ProductReviewCreate`, `ProductReviewUpdate`, and `ProductReviewModerate` mutations
- `saleor/graphql/product/schema.py` (modify) — Register new mutations and add a `productReviews` query with filtering and pagination
- `saleor/product/tests/test_review_models.py` (create) — Model-level tests for `ProductReview`
- `saleor/product/tests/test_review_services.py` (create) — Service-layer tests
- `saleor/graphql/product/tests/test_review_mutations.py` (create) — GraphQL mutation tests

## Requirements

### ProductReview Model

- Fields:
  - `product` — `ForeignKey` to `saleor.product.Product`, `on_delete=models.CASCADE`, `related_name="reviews"`
  - `user` — `ForeignKey` to the auth user model, `on_delete=models.CASCADE`, `related_name="product_reviews"`
  - `rating` — `PositiveSmallIntegerField` with validators enforcing range 1–5
  - `title` — `CharField(max_length=200)`
  - `body` — `TextField(blank=True)`
  - `status` — `CharField(max_length=20)` with choices `PENDING`, `APPROVED`, `REJECTED`, default `PENDING`
  - `created_at` — `DateTimeField(auto_now_add=True)`
  - `updated_at` — `DateTimeField(auto_now=True)`
- Constraints:
  - `UniqueConstraint` on `(product, user)` — one review per user per product
  - `CheckConstraint` ensuring `rating >= 1` and `rating <= 5`
- Indexes:
  - Composite index on `(product, status)` for filtered listing queries
  - Index on `created_at` descending for chronological ordering
- Custom `QuerySet`:
  - `.approved()` — filters to `status="APPROVED"`
  - `.for_product(product_id)` — filters by `product_id`
  - `.with_user()` — calls `select_related("user")` to prevent N+1 queries
  - `.average_rating()` — annotates/aggregates average rating for the queryset
- `Meta.ordering` set to `["-created_at"]`
- `__str__` returns `f"{self.user} - {self.product} ({self.rating}/5)"`

### Service Layer (services.py)

- `create_review(user, product_id, rating, title, body="")`:
  - Validates that the product exists; raises `Product.DoesNotExist` if not
  - Validates that the user has not already reviewed this product; raises `ValidationError` with message `"You have already reviewed this product"` if duplicate
  - Creates and returns the `ProductReview` with status `PENDING`
- `update_review(user, review_id, rating=None, title=None, body=None)`:
  - Only the original author can update; raises `PermissionError` if `review.user != user`
  - Only reviews with status `PENDING` can be updated; raises `ValidationError` with message `"Only pending reviews can be edited"` for `APPROVED` or `REJECTED` reviews
  - Updates only the supplied fields (non-None values)
  - Resets status to `PENDING` after any edit
- `moderate_review(review_id, new_status)`:
  - `new_status` must be `"APPROVED"` or `"REJECTED"`; raises `ValueError` for other values
  - Updates the review's status
- `get_product_rating_summary(product_id)`:
  - Returns a dict `{"average_rating": float|None, "total_reviews": int, "rating_distribution": {1: int, 2: int, 3: int, 4: int, 5: int}}`
  - Only counts `APPROVED` reviews
  - If no approved reviews exist, `average_rating` is `None` and all distribution counts are `0`
- All database writes in `create_review` and `update_review` must be wrapped in `transaction.atomic`

### GraphQL Schema

- `ProductReviewType`:
  - Fields: `id`, `rating`, `title`, `body`, `status`, `createdAt`, `updatedAt`, `user` (resolve to user display name)
- `ProductReviewCreate` mutation:
  - Input: `productId` (ID, required), `rating` (Int, required), `title` (String, required), `body` (String, optional)
  - Requires authenticated user; returns error for anonymous requests
  - Returns the created `ProductReviewType`
- `ProductReviewUpdate` mutation:
  - Input: `reviewId` (ID, required), `rating` (Int, optional), `title` (String, optional), `body` (String, optional)
  - Requires authenticated user who is the review author
- `ProductReviewModerate` mutation:
  - Input: `reviewId` (ID, required), `status` (enum `APPROVED`/`REJECTED`, required)
  - Requires staff permissions
- `productReviews` query:
  - Arguments: `productId` (ID, required), `status` (String, optional filter), `first`/`after` for cursor pagination
  - Returns paginated list of `ProductReviewType` ordered by `created_at` descending

### Expected Functionality

- Authenticated user creates a review with `rating=5, title="Great"` for product 1 → returns review with `status="PENDING"`
- Same user attempts second review for product 1 → error `"You have already reviewed this product"`
- User attempts to update someone else's review → `PermissionError`
- User updates their own `PENDING` review's title → status remains/resets to `PENDING`, title updated
- User attempts to update their own `APPROVED` review → error `"Only pending reviews can be edited"`
- Staff user moderates a review to `APPROVED` → status changes to `APPROVED`
- Staff user attempts to moderate with status `"INVALID"` → `ValueError`
- `get_product_rating_summary` for a product with approved reviews rated [5, 4, 4, 3, 5] → `{"average_rating": 4.2, "total_reviews": 5, "rating_distribution": {1: 0, 2: 0, 3: 1, 4: 2, 5: 2}}`
- `get_product_rating_summary` for a product with zero approved reviews → `{"average_rating": None, "total_reviews": 0, "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}}`
- GraphQL query `productReviews(productId: "1", status: "APPROVED")` → returns only approved reviews, paginated
- Anonymous user attempting `ProductReviewCreate` mutation → authentication error
- Review with `rating=0` or `rating=6` → validation error from `CheckConstraint`

## Acceptance Criteria

- `python manage.py makemigrations --check` reports no missing migrations
- `python -m pytest saleor/product/tests/test_review_models.py -v` passes all tests
- `python -m pytest saleor/product/tests/test_review_services.py -v` passes all tests
- `python -m pytest saleor/graphql/product/tests/test_review_mutations.py -v` passes all tests
- The `UniqueConstraint` on `(product, user)` prevents duplicate reviews at the database level
- The `CheckConstraint` on `rating` rejects values outside 1–5 at the database level
- The `with_user()` QuerySet method prevents N+1 queries when iterating reviews (verifiable via Django's `assertNumQueries`)
- Service functions use `transaction.atomic` for all write operations
- GraphQL mutations enforce authentication and authorization (author-only edit, staff-only moderation)
- All existing Saleor tests continue to pass without regressions
