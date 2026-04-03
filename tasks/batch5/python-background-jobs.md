# Task: Implement an Idempotent Data Export Task with State Management in Celery

## Background

Celery (https://github.com/celery/celery) is Python's standard distributed task queue. This task requires adding a complete, non-trivial example of a long-running data export task to the Celery examples directory. The export task must demonstrate proper state tracking, idempotent execution, retry handling, and progress reporting — capabilities that are critical in production Celery deployments but missing from the existing examples.

## Files to Create/Modify

- `examples/data_export/tasks.py` (create) — Defines the `DataExportTask` Celery task with state machine (PENDING → PROCESSING → COMPLETED / FAILED), idempotency key, and retry configuration.
- `examples/data_export/models.py` (create) — `ExportJob` model (using a simple SQLite-backed storage) tracking job ID, status, progress percentage, result URL, error message, and created/updated timestamps.
- `examples/data_export/celeryconfig.py` (create) — Celery configuration: broker URL, result backend, task serialization settings, and retry policy defaults.
- `examples/data_export/api.py` (create) — A minimal Flask or FastAPI app exposing `POST /exports` (submit), `GET /exports/{job_id}` (poll status), and `DELETE /exports/{job_id}` (cancel).
- `examples/data_export/tests/test_tasks.py` (create) — Tests covering the happy path, idempotent re-submission, retry on transient failure, state transitions, and cancellation.

## Requirements

### Task State Machine

- An export job transitions through states: `PENDING` → `PROCESSING` → `COMPLETED` or `FAILED`.
- The `PROCESSING` state reports progress as a percentage (0–100) that can be polled via the status API.
- A `FAILED` job records the error message and final state; it does not automatically re-enter `PROCESSING`.
- A `COMPLETED` job stores a `result_url` (simulated file path).

### Idempotency

- Each export request includes an `idempotency_key` (caller-provided string).
- If a task with the same `idempotency_key` already exists and is in `PENDING` or `PROCESSING` state, the submission returns the existing job ID instead of creating a duplicate.
- If the existing job is in `COMPLETED` or `FAILED` state, a new job may be created with the same key.

### Retry Behavior

- The task retries up to 3 times on `IOError` and `ConnectionError` (simulating transient downstream failures).
- The delay between retries follows exponential backoff: 10s, 30s, 90s.
- After the final retry failure, the job transitions to `FAILED` with the error details.
- Retries must not produce duplicate side effects (the export write operation is idempotent — writing the same data to the same path is safe).

### Cancellation

- `DELETE /exports/{job_id}` sets the job state to `CANCELLED`.
- The task checks for cancellation at each progress checkpoint (simulated every 10% of processing); if cancelled, it stops processing and transitions to `CANCELLED` state.
- Cancelling an already-completed or already-failed job returns 409 Conflict.

### Expected Functionality

- `POST /exports` with `{ "query": "SELECT * FROM users", "idempotency_key": "abc-123" }` → 202 Accepted with `{ "job_id": "...", "status": "PENDING" }`.
- Repeated `POST` with same `idempotency_key` while job is running → returns same `job_id`.
- `GET /exports/{job_id}` during processing → `{ "status": "PROCESSING", "progress": 40 }`.
- `GET /exports/{job_id}` after completion → `{ "status": "COMPLETED", "result_url": "/exports/files/abc-123.csv" }`.
- Task encounters `IOError` on first attempt, succeeds on retry → job eventually reaches `COMPLETED`.
- `DELETE /exports/{job_id}` while processing → job stops at next checkpoint, status becomes `CANCELLED`.

## Acceptance Criteria

- The task transitions through `PENDING → PROCESSING → COMPLETED` on a successful run.
- Submitting a duplicate `idempotency_key` for an in-progress job returns the existing job without creating a new task.
- The task retries up to 3 times on `IOError`/`ConnectionError` with increasing delays, then moves to `FAILED`.
- `DELETE` cancels a running job at the next progress checkpoint; cancelling a completed job returns 409.
- Progress is reported incrementally and can be polled via `GET /exports/{job_id}`.
- Tests cover: happy path, idempotent re-submission, retry + eventual success, retry exhaustion → FAILED, and cancellation.
