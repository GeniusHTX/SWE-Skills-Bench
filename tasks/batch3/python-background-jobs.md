# Task: Implement an Idempotent Task State Machine for Celery Email Delivery Pipeline

## Background

Celery (https://github.com/celery/celery) is a distributed task queue for Python. The project needs a robust email delivery pipeline that handles transient SMTP failures, tracks delivery state across retries, and ensures emails are never sent twice even if the same task is dispatched multiple times. This pipeline must integrate with Celery's existing task infrastructure and provide visibility into delivery status.

## Files to Create/Modify

- `celery/contrib/email_pipeline.py` (create) — Email delivery task with state machine, idempotency enforcement, and configurable retry behavior
- `celery/contrib/email_models.py` (create) — Data models for email delivery records and state transitions
- `t/unit/contrib/test_email_pipeline.py` (create) — Tests covering state transitions, idempotency, retry behavior, timeout, and failure scenarios

## Requirements

### Email Delivery State Machine

- Define delivery states: `PENDING`, `SENDING`, `SENT`, `FAILED`, `CANCELLED`
- Valid transitions: `PENDING→SENDING`, `SENDING→SENT`, `SENDING→FAILED`, `SENDING→PENDING` (for retry), `PENDING→CANCELLED`, `FAILED→PENDING` (for manual retry)
- Invalid transitions (e.g., `SENT→SENDING`, `CANCELLED→SENDING`) must raise `InvalidStateTransition` with a message indicating the current and attempted states
- Each state transition must record a timestamp and optional metadata (e.g., error message for `FAILED`)

### Idempotency

- Each email delivery request is identified by an `idempotency_key` (string, provided by the caller)
- If a task with the same `idempotency_key` is already in `SENT` state, the task returns immediately without resending
- If a task with the same `idempotency_key` is in `SENDING` state, the task raises `DuplicateDeliveryError`
- The idempotency check and state transition to `SENDING` must be atomic to prevent race conditions

### Retry Behavior

- On transient SMTP errors (`SMTPTemporaryError`, `ConnectionError`, `TimeoutError`), transition to `PENDING` and schedule a retry
- Maximum 5 retry attempts with exponentially increasing delays (starting at 60 seconds, capped at 3600 seconds)
- On permanent SMTP errors (`SMTPAuthenticationError`, `SMTPRecipientsRefused`), transition to `FAILED` immediately without retry
- After exhausting all retries, transition to `FAILED` and log the failure at ERROR level

### Soft and Hard Timeouts

- Each delivery attempt has a soft timeout of 30 seconds that triggers a warning log and allows the task to attempt graceful cancellation
- Each delivery attempt has a hard timeout of 60 seconds that forcibly terminates the attempt and transitions to `PENDING` for retry

### Status Visibility

- Provide a `get_delivery_status(idempotency_key)` function that returns the current state, attempt count, last error message, and full transition history
- Provide a `list_failed_deliveries(since: datetime)` function that returns all deliveries in `FAILED` state since the given timestamp

### Expected Functionality

- Submitting a delivery with key "order-123-confirm" sends the email and transitions through `PENDING→SENDING→SENT`
- Submitting the same key "order-123-confirm" again returns immediately without sending
- A delivery that fails with `ConnectionError` retries up to 5 times with increasing delays
- A delivery that fails with `SMTPRecipientsRefused` transitions to `FAILED` immediately
- Calling `get_delivery_status("order-123-confirm")` returns `{"state": "SENT", "attempts": 1, "last_error": null, "history": [...]}`
- An attempt to transition from `SENT` to `SENDING` raises `InvalidStateTransition`
- Two concurrent tasks with the same key: the second receives `DuplicateDeliveryError`

## Acceptance Criteria

- State machine enforces all valid/invalid transitions and raises `InvalidStateTransition` for illegal ones
- Idempotency prevents duplicate sends for the same `idempotency_key`
- Transient SMTP errors trigger retry with exponential backoff; permanent errors fail immediately
- Retry count is capped at 5 and delay is capped at 3600 seconds
- Soft timeout logs a warning at 30 seconds; hard timeout terminates at 60 seconds
- `get_delivery_status` returns accurate state, attempt count, error, and transition history
- `list_failed_deliveries` returns correct results filtered by timestamp
- All state transitions, idempotency, timeout, and error scenarios are covered by tests
