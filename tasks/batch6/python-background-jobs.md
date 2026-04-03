# Task: Implement Multi-Step Order Processing Pipeline with Celery

## Background

The Celery project (https://github.com/celery/celery) is a distributed task queue for Python. A new multi-step order processing pipeline is needed to demonstrate real-world task chaining, idempotent execution, error handling with callbacks, and job state tracking. The pipeline processes an e-commerce order through sequential stages: validation, payment, inventory reservation, and notification — each as a separate Celery task.

## Files to Create/Modify

- `examples/order_pipeline/tasks.py` (create) — Celery task definitions for each pipeline stage: `validate_order`, `process_payment`, `reserve_inventory`, `send_notification`
- `examples/order_pipeline/models.py` (create) — Data models for Order, OrderStatus enum, PaymentResult, and job state tracking
- `examples/order_pipeline/pipeline.py` (create) — Pipeline orchestrator that chains the tasks, configures error callbacks, and exposes a `submit_order` function returning a job ID
- `examples/order_pipeline/config.py` (create) — Celery configuration with appropriate task serialization, retry settings, time limits, and acknowledgment behavior
- `tests/test_order_pipeline.py` (create) — Unit tests for task idempotency, error callback execution, state transitions, and end-to-end pipeline flow

## Requirements

### Order Model and State Machine

- Define an `OrderStatus` enum with states: `PENDING`, `VALIDATING`, `PAYMENT_PROCESSING`, `RESERVING_INVENTORY`, `SENDING_NOTIFICATION`, `COMPLETED`, `FAILED`.
- Each order is identified by a string `order_id` and carries: `customer_id`, `items` (list of dicts with `product_id`, `quantity`, `unit_price`), `total_amount`, `status`, `created_at`, `updated_at`, and optional `error_message`.
- State transitions must be enforced — e.g., `PAYMENT_PROCESSING` can only transition to `RESERVING_INVENTORY` or `FAILED`, not back to `PENDING`.

### Task Definitions

- `validate_order(order_id: str)`:
  - Checks that items list is non-empty, all quantities are positive, all unit prices are non-negative, and `total_amount` matches the sum of `quantity × unit_price` across all items.
  - On validation failure: transitions to `FAILED` with a descriptive error message.
  - On success: transitions to `PAYMENT_PROCESSING`.

- `process_payment(order_id: str)`:
  - Simulates payment processing. Must use an idempotency key (`f"payment-{order_id}"`) so retries do not double-charge.
  - Must be configured with `autoretry_for=(ConnectionError, TimeoutError)`, `max_retries=3`, and exponential backoff starting at 60 seconds.
  - On permanent failure (e.g., `PaymentDeclinedError`): transitions to `FAILED` without retry.
  - On success: stores a `transaction_id` and transitions to `RESERVING_INVENTORY`.

- `reserve_inventory(order_id: str)`:
  - For each item, attempts to reserve the requested quantity. If any item has insufficient stock, transitions to `FAILED` with a message indicating which product failed.
  - Must be idempotent: re-executing for an already-reserved order returns immediately without double-reserving.
  - On success: transitions to `SENDING_NOTIFICATION`.

- `send_notification(order_id: str)`:
  - Sends an order confirmation notification. Notification failures must NOT fail the overall order — log a warning and transition to `COMPLETED` regardless.
  - On success: transitions to `COMPLETED`.

### Pipeline Orchestration

- `submit_order(order_data: dict) -> str`:
  - Creates an order record with status `PENDING`, generates a UUID `order_id`.
  - Chains the four tasks using Celery's `chain()` primitive: `validate_order | process_payment | reserve_inventory | send_notification`.
  - Attaches an `on_error` callback named `handle_pipeline_error` that transitions the order to `FAILED` and records which stage failed with the exception message.
  - Returns the `order_id` immediately.

- A `get_order_status(order_id: str) -> dict` function must return the current order state including status, error message (if any), and timestamps.

### Celery Configuration

- Task serializer: `json`.
- `task_acks_late`: `True` (acknowledge after completion).
- `task_reject_on_worker_lost`: `True`.
- `worker_prefetch_multiplier`: `1`.
- `task_time_limit`: 300 seconds (hard).
- `task_soft_time_limit`: 240 seconds (soft).

### Expected Functionality

- Submitting a valid order → pipeline runs through all four stages, final status is `COMPLETED`, timestamps are recorded for each transition.
- Submitting an order with `items: []` → validate_order transitions to `FAILED` with error `"Order must contain at least one item"`.
- Submitting an order where total_amount is 100 but items sum to 80 → validate_order transitions to `FAILED` with error containing `"total_amount mismatch"`.
- Payment service raises `ConnectionError` → task retries up to 3 times with exponential backoff.
- Payment service raises `PaymentDeclinedError` → task transitions to `FAILED` immediately without retry.
- Calling `process_payment` twice for the same order_id → second call detects existing transaction and returns without re-processing.
- Inventory reservation fails for one item → order transitions to `FAILED` with message `"Insufficient stock for product_id=XYZ"`.
- Notification failure → order still transitions to `COMPLETED`, warning is logged.

## Acceptance Criteria

- Four Celery tasks implement the complete order lifecycle with correct state transitions enforced at each step.
- The pipeline uses Celery's `chain()` to sequence tasks and an `on_error` callback to handle failures at any stage.
- `process_payment` and `reserve_inventory` are idempotent — re-execution for an already-processed order produces no side effects.
- Payment retries use exponential backoff for transient errors and fail immediately for permanent errors.
- Notification failures do not prevent the order from reaching `COMPLETED` status.
- `submit_order` returns a job ID immediately; `get_order_status` reflects the current pipeline stage and any error information.
- All tasks respect the configured time limits, acknowledgment settings, and serialization format.
