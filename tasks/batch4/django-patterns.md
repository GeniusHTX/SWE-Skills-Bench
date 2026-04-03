# Task: Implement Product Review System with Service Layer in Saleor

## Background

The Saleor e-commerce platform (https://github.com/saleor/saleor) needs a product review system that allows authenticated customers to submit, update, and delete reviews for products they have purchased. The feature requires a Django model with proper field configuration, a DRF REST API with nested serializers, a service layer for business logic, queryset optimization, and caching of aggregated review data.

## Files to Create/Modify

- `saleor/product/models.py` (modify) — Add `ProductReview` model with foreign keys to `Product` and `User`, rating, title, body, status, and timestamps
- `saleor/product/managers.py` (modify) — Add custom manager and queryset for `ProductReview` with annotation and filtering methods
- `saleor/product/api/serializers.py` (create or modify) — DRF serializers for review creation, update, listing, and aggregated stats
- `saleor/product/api/views.py` (create or modify) — DRF ViewSet with list, create, update, partial_update, and destroy actions
- `saleor/product/api/urls.py` (create or modify) — URL routing for the review endpoints nested under products
- `saleor/product/services.py` (create) — Service layer with review submission, moderation, and aggregation logic
- `saleor/product/signals.py` (modify) — Signal handlers to update cached review aggregates when reviews change

## Requirements

### Model Design

- `ProductReview` fields: `id` (auto PK), `product` (FK to Product, `on_delete=CASCADE`, `related_name="reviews"`), `user` (FK to User, `on_delete=CASCADE`), `rating` (PositiveSmallIntegerField, validators 1–5), `title` (CharField max 200), `body` (TextField, max 5000 chars), `status` (CharField choices: `pending`, `approved`, `rejected`, default `pending`), `created_at` (auto_now_add), `updated_at` (auto_now)
- Add a unique constraint on `(product, user)` so each user can only review a product once
- Add a database index on `(product, status, created_at)` for efficient filtered listing

### Custom QuerySet

- `approved()` — filters to `status="approved"`
- `for_product(product_id)` — filters by product
- `with_user_info()` — uses `select_related("user")` to avoid N+1 queries
- `aggregate_stats()` — annotates with `avg_rating` and `review_count` using Django aggregation functions

### Service Layer

- `submit_review(user, product_id, rating, title, body)`:
  - Verifies the user has at least one completed order containing the product; raises `PermissionDenied` if not
  - Checks the unique constraint; raises `ValidationError` if the user already reviewed this product
  - Creates the review with `status="pending"`
- `moderate_review(review_id, new_status, moderator)`:
  - Only users with `product.manage_reviews` permission can moderate; raises `PermissionDenied` otherwise
  - Updates the review status and logs the moderator's action
- `get_product_review_summary(product_id)`:
  - Returns `{ "average_rating": float, "total_reviews": int, "rating_distribution": {1: n, 2: n, 3: n, 4: n, 5: n} }`
  - Result is cached; cache invalidation occurs when a review for the product is created, updated, or deleted

### API Endpoints

- `GET /api/products/{product_id}/reviews/` — paginated list of approved reviews with user display name, rating, title, body, created_at; ordered by `-created_at`
- `GET /api/products/{product_id}/reviews/summary/` — aggregated review stats (average rating, total count, distribution)
- `POST /api/products/{product_id}/reviews/` — submit a review (authenticated, must have purchased product)
- `PATCH /api/products/{product_id}/reviews/{id}/` — update own review (only title and body, not rating; only while status is `pending`)
- `DELETE /api/products/{product_id}/reviews/{id}/` — delete own review
- POST with duplicate product+user returns `409 Conflict`
- POST by a user who has not purchased the product returns `403 Forbidden`

### Caching

- `get_product_review_summary` must cache results per product; cache timeout 1 hour
- `post_save` and `post_delete` signals on `ProductReview` must invalidate the summary cache for the affected product

### Expected Functionality

- A user who purchased Product A submits a review with rating 4 — review is created with `status="pending"` and returns `201`
- The same user attempts a second review for Product A — returns `409` with message about existing review
- A user who never purchased Product B attempts a review — returns `403`
- `GET /api/products/1/reviews/` returns only approved reviews, each with user info loaded efficiently (no N+1)
- `GET /api/products/1/reviews/summary/` returns correct average and distribution; a second call within 1 hour returns cached data
- After a review is approved by a moderator, the summary cache is invalidated and the next summary request reflects the new review
- PATCH of a review in `approved` status returns `400` (edits only allowed while `pending`)

## Acceptance Criteria

- `ProductReview` model has correct fields, validators, unique constraint, and index
- Custom queryset methods provide filtered, annotated querysets without N+1 queries
- Service layer enforces purchase verification, duplicate prevention, and moderation permissions
- API endpoints return correct status codes for valid submissions (201), duplicates (409), unauthorized (403), and edit restrictions (400)
- Review listing returns only approved reviews with related user data eagerly loaded
- Summary endpoint returns correct aggregation and uses caching with proper invalidation on review changes
- Signal handlers invalidate the review summary cache when reviews are saved or deleted
