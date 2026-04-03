# Task: Add a Product Reviews Feature to Saleor Using Django Patterns

## Background

Saleor (https://github.com/saleor/saleor) is a headless e-commerce platform built with Django and GraphQL. A new product reviews feature is needed, following Saleor's established patterns: Django models with proper managers, GraphQL types with dataloader-based resolution, GraphQL mutations extending `BaseMutation`, Celery tasks for async processing, and comprehensive test coverage.

## Files to Create/Modify

- `saleor/product/models.py` (modify) — Add `ProductReview` model with fields: `id` (UUID, primary key), `product` (ForeignKey to Product), `user` (ForeignKey to User, nullable for anonymous), `rating` (PositiveSmallIntegerField, validators 1–5), `title` (CharField, max 200), `content` (TextField), `status` (CharField choices: PENDING, APPROVED, REJECTED, default PENDING), `created_at`, `updated_at`. Add `ProductReviewQueryset` custom manager with `approved()`, `pending()`, `for_product(product_id)` methods
- `saleor/product/migrations/0XXX_add_product_review.py` (create) — Django migration for the ProductReview model and its database index on `(product_id, status, created_at)`
- `saleor/graphql/product/types/product_review.py` (create) — GraphQL type `ProductReview` with all fields, using a dataloader for the `product` and `user` fields to avoid N+1 queries
- `saleor/graphql/product/mutations/product_review.py` (create) — GraphQL mutations: `ProductReviewCreate` (authenticated users submit reviews), `ProductReviewApprove` (staff-only), `ProductReviewDelete` (staff-only)
- `saleor/graphql/product/schema.py` (modify) — Register the new queries (resolve reviews for a product) and mutations in `ProductMutations`
- `saleor/graphql/product/dataloaders/product_reviews.py` (create) — Dataloader that batches product review queries by product ID to resolve `Product.reviews` efficiently
- `saleor/product/tasks.py` (modify) — Add `update_product_average_rating` Celery task that recalculates and caches the average rating after a review is approved
- `saleor/product/signals.py` (modify) — Add a `post_save` signal on `ProductReview` that triggers the `update_product_average_rating` task when status changes to APPROVED

## Requirements

### Model Design

- `ProductReview` must use a UUID primary key (`models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`)
- `rating` must be constrained with `MinValueValidator(1)` and `MaxValueValidator(5)`
- `status` must use a `TextChoices` enum: `PENDING = "pending"`, `APPROVED = "approved"`, `REJECTED = "rejected"`
- `Meta.ordering` must be `["-created_at"]`
- `Meta.indexes` must include a composite index on `["product", "status", "created_at"]`
- `ProductReviewQueryset.approved()` returns reviews with `status=APPROVED`
- `ProductReviewQueryset.for_product(product_id)` filters by `product_id`
- One user can only submit one review per product (unique constraint on `product` + `user`)

### GraphQL Types

- `ProductReview` type must expose: `id`, `rating`, `title`, `content`, `status`, `createdAt`, `updatedAt`, `user` (nullable, resolved via dataloader), `product` (resolved via dataloader)
- `Product` type must gain a new `reviews` field returning `[ProductReview!]!` with optional `status` filter argument
- The `reviews` field must use `ProductReviewsByProductIdLoader` to batch-load reviews

### GraphQL Mutations

- `ProductReviewCreate` — Input: `productId` (ID!), `rating` (Int!), `title` (String!), `content` (String!). Requires authenticated user. Creates review with `status=PENDING`. Returns the created `ProductReview`. Fails with error if user already reviewed this product
- `ProductReviewApprove` — Input: `id` (ID!). Requires staff permission `MANAGE_PRODUCTS`. Sets `status=APPROVED`. Triggers average rating recalculation task
- `ProductReviewDelete` — Input: `id` (ID!). Requires staff permission `MANAGE_PRODUCTS`. Deletes the review. Returns the deleted review data

### Background Task

- `update_product_average_rating(product_id)` — Queries all approved reviews for the product, computes average rating rounded to 1 decimal place, stores it via `Product.objects.filter(id=product_id).update(rating=avg)` (assumes a `rating` field on Product, which must also be added as `DecimalField(max_digits=2, decimal_places=1, null=True)`)
- The task must be idempotent — running it twice produces the same result

### Expected Functionality

- An authenticated user creates a review for product ID 1 with rating 5 — the review is saved with `status=PENDING`
- A staff user approves the review — status changes to `APPROVED` and the product's average rating is updated asynchronously
- Querying `product.reviews(status: APPROVED)` returns only approved reviews via dataloader
- Attempting to create a second review for the same product by the same user returns a validation error

## Acceptance Criteria

- `ProductReview` model migrates cleanly and includes UUID primary key, rating validators, status choices, and unique constraint on (product, user)
- GraphQL mutations enforce authentication (user) and staff permissions (approve/delete) correctly
- Dataloader resolves `Product.reviews` without N+1 queries when querying multiple products
- The Celery task computes correct average ratings and is idempotent
- The `post_save` signal triggers the task only when status transitions to APPROVED
- `python -m pytest /workspace/tests/test_django_patterns.py -v --tb=short` passes
