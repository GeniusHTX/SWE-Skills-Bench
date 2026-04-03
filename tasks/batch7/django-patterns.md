# Task: Add a Product Bundle Feature to the Saleor E-Commerce Platform

## Background

Saleor (https://github.com/saleor/saleor) is a high-performance Django-based e-commerce platform. The task is to add a Product Bundle feature that allows grouping multiple products into a single purchasable bundle with a discount. This involves creating Django models, custom QuerySet managers, a service layer for business logic, signals for inventory synchronization, and GraphQL mutations/queries.

## Files to Create/Modify

- `saleor/product/models.py` (modify) — Add `ProductBundle` and `BundleItem` models with proper field configuration, Meta classes, indexes, and constraints
- `saleor/product/managers.py` (create) — Custom QuerySet and Manager for `ProductBundle` with chainable query methods
- `saleor/product/services.py` (create) — Service layer for bundle CRUD operations, pricing calculations, and availability checks
- `saleor/product/signals.py` (modify or create) — Signals to synchronize bundle availability when component product stock changes
- `saleor/graphql/product/mutations/bundles.py` (create) — GraphQL mutations for creating, updating, and deleting bundles
- `saleor/graphql/product/types/bundles.py` (create) — GraphQL type definitions for `ProductBundle` and `BundleItem`

## Requirements

### Models (`models.py`)

#### `ProductBundle`
- `name` — `CharField(max_length=250)`
- `slug` — `SlugField(unique=True, max_length=255)`
- `description` — `TextField(blank=True, default="")`
- `discount_type` — `CharField` with choices: `"percentage"`, `"fixed_amount"`
- `discount_value` — `DecimalField(max_digits=12, decimal_places=3, validators=[MinValueValidator(Decimal("0"))])`
- `currency` — `CharField(max_length=3)` (ISO 4217 currency code, required when `discount_type` is `"fixed_amount"`)
- `is_active` — `BooleanField(default=True)`
- `created_at` — `DateTimeField(auto_now_add=True)`
- `updated_at` — `DateTimeField(auto_now=True)`
- Meta: `ordering = ["-created_at"]`, `db_table = "product_bundle"`, indexes on `slug`, `is_active`, and `created_at`
- Constraint: `discount_value` must be non-negative (`CheckConstraint`)
- Constraint: when `discount_type` is `"percentage"`, `discount_value` must be ≤ 100

#### `BundleItem`
- `bundle` — `ForeignKey(ProductBundle, on_delete=CASCADE, related_name="items")`
- `product` — `ForeignKey("product.Product", on_delete=CASCADE, related_name="bundle_items")`
- `quantity` — `PositiveIntegerField(default=1)`
- `sort_order` — `IntegerField(default=0)`
- Meta: `ordering = ["sort_order"]`, `db_table = "product_bundle_item"`, unique constraint on `(bundle, product)`

### Custom QuerySet and Manager (`managers.py`)

Implement `ProductBundleQuerySet` with these chainable methods:
- `active()` — Filters to `is_active=True` bundles
- `with_items()` — Prefetches related `items` and their `product` foreign keys in a single query
- `available()` — Filters to bundles where every component product has `stock >= bundle_item.quantity`
- `in_currency(currency_code)` — Filters bundles that have either no fixed discount or a matching currency
- `search(query)` — Filters bundles by name or description (case-insensitive contains)

Expose via `ProductBundle.objects = ProductBundleQuerySet.as_manager()`

### Service Layer (`services.py`)

Implement `BundleService` class with static methods:

- `create_bundle(name, slug, discount_type, discount_value, items, currency=None)`:
  - Creates a `ProductBundle` and associated `BundleItem` records in a single atomic transaction
  - `items` is a list of dicts: `[{"product_id": int, "quantity": int, "sort_order": int}, ...]`
  - Validates that all product IDs exist; raises `ValidationError` if any do not
  - Returns the created `ProductBundle` instance with items prefetched

- `calculate_bundle_price(bundle)`:
  - Sums the prices of all component products multiplied by their quantities
  - Applies the discount: if `"percentage"`, reduces the total by that percentage; if `"fixed_amount"`, subtracts the fixed value (minimum total is 0)
  - Returns a `Decimal` representing the final bundle price

- `check_availability(bundle)`:
  - Returns `True` if every component product has sufficient stock for the required quantity
  - Returns `False` otherwise

- `update_bundle_items(bundle, items)`:
  - Replaces all existing `BundleItem` records for the bundle with the new list in an atomic transaction
  - Follows delete-then-create pattern within the transaction

### Signals (`signals.py`)

- Connect a `post_save` signal on the `Product` model (specifically on stock-related changes)
- When a product's stock drops below the quantity required by any bundle, set those bundles' `is_active` to `False`
- When a product's stock increases to satisfy all bundle requirements, set those bundles' `is_active` to `True`
- Register the signal handler in the `ProductConfig.ready()` method in `saleor/product/apps.py`

### GraphQL Types (`types/bundles.py`)

- `BundleItemType`: exposes `product`, `quantity`, `sort_order`
- `ProductBundleType`: exposes `id`, `name`, `slug`, `description`, `discount_type`, `discount_value`, `currency`, `is_active`, `items` (list of `BundleItemType`), `total_price` (computed field using `BundleService.calculate_bundle_price`), `is_available` (computed field using `BundleService.check_availability`)

### GraphQL Mutations (`mutations/bundles.py`)

- `BundleCreate`: accepts `name`, `slug`, `discount_type`, `discount_value`, `currency`, `items` (list of `{product_id, quantity, sort_order}`); returns `ProductBundleType`
- `BundleUpdate`: accepts `id`, optional `name`, `slug`, `discount_type`, `discount_value`, `is_active`, `items`; returns `ProductBundleType`
- `BundleDelete`: accepts `id`; deletes the bundle and all associated items; returns `{success: true}`

## Expected Functionality

- Creating a bundle with two products (Product A at $10 × 2, Product B at $25 × 1) with a 10% discount yields a bundle price of $40.50
- Querying `ProductBundle.objects.active().available().with_items()` returns only bundles that are active and have all components in stock, with items prefetched
- Reducing Product A's stock to 0 triggers the signal, which deactivates any bundle containing Product A
- Restoring Product A's stock reactivates the bundle if all other components are also in stock
- The `BundleCreate` GraphQL mutation creates a bundle with items in a single atomic operation

## Acceptance Criteria

- `ProductBundle` and `BundleItem` models have all specified fields, indexes, and constraints
- `ProductBundleQuerySet` methods are chainable and produce correct SQL queries
- `BundleService.create_bundle` creates a bundle with items atomically and validates product existence
- `BundleService.calculate_bundle_price` returns correct prices for both percentage and fixed-amount discounts
- `BundleService.check_availability` correctly reflects component product stock levels
- The `post_save` signal activates/deactivates bundles when component product stock changes
- GraphQL types expose computed `total_price` and `is_available` fields
- GraphQL mutations perform CRUD operations with proper validation and error handling
- All operations are covered by unit tests
