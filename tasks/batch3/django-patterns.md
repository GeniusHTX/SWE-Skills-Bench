# Task: Implement Product Review System with GraphQL API in Saleor

## Background

Saleor (https://github.com/saleor/saleor) is a high-performance, headless commerce platform built with Django and GraphQL. The platform currently lacks a native product review system. A new `review` Django app needs to be added that allows authenticated customers to submit reviews for products they have purchased, with moderation capabilities for staff users, and a GraphQL API exposing review data for storefronts.

## Files to Create/Modify

- `saleor/review/__init__.py` (create) — Package init for the review app
- `saleor/review/models.py` (create) — Review and ReviewVote models with proper field definitions, indexes, and constraints
- `saleor/review/migrations/0001_initial.py` (create) — Initial migration for the review models
- `saleor/graphql/review/__init__.py` (create) — Package init for graphql review module
- `saleor/graphql/review/types.py` (create) — GraphQL object types for Review and ReviewVote
- `saleor/graphql/review/mutations.py` (create) — GraphQL mutations: ReviewCreate, ReviewUpdate, ReviewDelete, ReviewModerate, ReviewVote
- `saleor/graphql/review/resolvers.py` (create) — Query resolvers for reviews with filtering and sorting
- `saleor/graphql/review/schema.py` (create) — ReviewQueries and ReviewMutations classes to register in the root schema
- `saleor/graphql/schema.py` (modify) — Register review queries and mutations in the root schema
- `saleor/settings.py` (modify) — Add `saleor.review` to INSTALLED_APPS

## Requirements

### Review Model

- A `Review` model with fields: `product` (ForeignKey to `product.Product`), `user` (ForeignKey to `account.User`), `rating` (PositiveSmallIntegerField, 1–5), `title` (CharField, max 200), `body` (TextField), `status` (CharField with choices: `PENDING`, `APPROVED`, `REJECTED`), `created_at` (DateTimeField, auto), `updated_at` (DateTimeField, auto)
- Enforce a unique constraint on `(product, user)` — one review per user per product
- Add a database check constraint ensuring `rating` is between 1 and 5
- Add indexes on `product`, `user`, `status`, and `created_at`
- A `ReviewVote` model with fields: `review` (ForeignKey to `Review`), `user` (ForeignKey to `account.User`), `is_helpful` (BooleanField)
- Enforce a unique constraint on `(review, user)` — one vote per user per review

### GraphQL Queries

- `review(id: ID!)` — Retrieve a single review by ID; only `APPROVED` reviews are visible to non-staff users
- `reviews(product: ID, user: ID, status: ReviewStatus, sortBy: ReviewSortingInput, first: Int, after: String)` — Paginated list of reviews with cursor-based pagination; non-staff users can only see `APPROVED` reviews; staff users can filter by any status
- Sorting must support: `CREATED_AT`, `RATING`, `HELPFUL_COUNT`
- Each `Review` GraphQL type must expose computed fields: `helpfulCount` (number of `is_helpful=True` votes) and `notHelpfulCount`

### GraphQL Mutations

- `reviewCreate(input: ReviewCreateInput!)` — Authenticated users only; creates a review in `PENDING` status; the user must have at least one fulfilled order containing the reviewed product; returns validation error if the user already reviewed the product
- `reviewUpdate(id: ID!, input: ReviewUpdateInput!)` — Only the review author or staff; allows updating `rating`, `title`, and `body`; resets status to `PENDING` if the author edits it
- `reviewDelete(id: ID!)` — Only the review author or staff; performs hard delete
- `reviewModerate(id: ID!, status: ReviewStatus!)` — Staff only; sets review status to `APPROVED` or `REJECTED`
- `reviewVote(id: ID!, isHelpful: Boolean!)` — Authenticated users only; creates or updates a vote on a review; users cannot vote on their own reviews

### Permissions and Validation

- All mutations except `reviewVote` and `reviewCreate` require either ownership or the `MANAGE_PRODUCTS` permission for staff access
- `reviewCreate` must verify the user has purchased the product by checking for at least one `order.Order` in `FULFILLED` status with an `OrderLine` referencing the product
- When a non-staff user queries reviews, only `APPROVED` reviews are returned; staff users with `MANAGE_PRODUCTS` see all statuses
- `reviewVote` must reject votes on the user's own review with a validation error

### Expected Functionality

- An authenticated customer who has a fulfilled order for product X submits a review → review is created with `PENDING` status and is not visible in public queries
- The same customer tries to submit a second review for product X → receives a validation error about duplicate review
- A customer without any fulfilled order for product Y tries to submit a review → receives a validation error about purchase requirement
- A staff user calls `reviewModerate` with `APPROVED` → the review becomes visible in public `reviews` queries
- A customer edits their own approved review → status resets to `PENDING`
- A customer votes `isHelpful: true` on another user's review → `helpfulCount` increments by 1
- A customer tries to vote on their own review → receives a validation error
- A non-staff user queries `reviews` with `status: REJECTED` filter → filter is ignored, only `APPROVED` reviews are returned
- A staff user queries `reviews` with `status: REJECTED` → only rejected reviews are returned

## Acceptance Criteria

- The `Review` and `ReviewVote` models have the specified fields, constraints, and indexes, and migrations apply cleanly
- The GraphQL schema includes `review` and `reviews` queries and all five mutations
- `reviewCreate` enforces the purchase verification and duplicate-review constraint
- Moderation workflow transitions reviews between `PENDING`, `APPROVED`, and `REJECTED` statuses correctly
- Author edits to an approved review reset status to `PENDING`
- Non-staff users can only see `APPROVED` reviews in queries; staff users see all statuses
- `reviewVote` prevents self-voting and correctly updates `helpfulCount` / `notHelpfulCount` computed fields
- Cursor-based pagination and sorting by `CREATED_AT`, `RATING`, and `HELPFUL_COUNT` work correctly
- Permission checks enforce `MANAGE_PRODUCTS` for staff-only operations
