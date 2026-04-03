# Task: Add an Async Report Export Pipeline to Celery

## Background

Celery (https://github.com/celery/celery) is a distributed task queue. A new example module is needed that demonstrates production-grade background job patterns: task chaining, retry with exponential backoff, idempotent execution, job state tracking, and result aggregation. The example implements an async report export pipeline where a user requests a CSV export, the system processes it in stages (query data, transform, write CSV, upload to S3), and the user polls for completion status.

## Files to Create/Modify

- `examples/report_export/__init__.py` (create) — Package init
- `examples/report_export/app.py` (create) — Celery app configuration with Redis broker, result backend, task serializer (JSON), and task routes
- `examples/report_export/tasks.py` (create) — Task definitions: `query_data`, `transform_data`, `write_csv`, `upload_to_storage`, `export_report` (orchestrator using chain)
- `examples/report_export/models.py` (create) — Job state model: `ExportJob` dataclass with id, status, progress, result_url, error, timestamps
- `examples/report_export/store.py` (create) — In-memory job store (dict-based) with `create_job`, `update_job`, `get_job` functions (thread-safe with `threading.Lock`)
- `examples/report_export/api.py` (create) — FastAPI endpoints: `POST /exports` (start export), `GET /exports/{job_id}` (poll status)
- `tests/test_report_export.py` (create) — Tests for task logic, job state transitions, retry behavior, and idempotency

## Requirements

### Celery App Configuration (`app.py`)

- Broker URL from environment variable `CELERY_BROKER_URL` with default `redis://localhost:6379/0`
- Result backend from `CELERY_RESULT_BACKEND` with default `redis://localhost:6379/1`
- `task_serializer = "json"`, `result_serializer = "json"`, `accept_content = ["json"]`
- `task_acks_late = True` (acknowledge after completion for at-least-once delivery)
- `task_reject_on_worker_lost = True`
- `task_track_started = True`
- `worker_prefetch_multiplier = 1` (fair scheduling)

### Task Definitions (`tasks.py`)

- `query_data(job_id: str, query_params: dict) -> dict` — Simulates querying a database. Accepts `table`, `filters`, `columns` in query_params. Returns `{"rows": [...], "row_count": N}`. Updates job progress to 25%. Retries up to 3 times with exponential backoff (`2 ** retry_count` seconds) on `ConnectionError`
- `transform_data(query_result: dict, job_id: str) -> dict` — Applies transformations: filter null rows, format dates (ISO 8601), convert numeric strings to floats. Returns `{"rows": [...], "row_count": N}`. Updates job progress to 50%
- `write_csv(transform_result: dict, job_id: str) -> str` — Writes rows to a CSV file at `/tmp/exports/{job_id}.csv` using `csv.DictWriter`. Returns the file path. Updates job progress to 75%
- `upload_to_storage(csv_path: str, job_id: str) -> str` — Simulates uploading to S3 by copying file to `/tmp/exports/uploaded/{job_id}.csv`. Returns the "URL" string `f"s3://exports/{job_id}.csv"`. Updates job progress to 100% and sets status to SUCCEEDED with result_url. Must be idempotent — if the destination file already exists, return the URL without re-uploading
- `export_report(job_id: str, query_params: dict)` — Orchestrator that chains all four tasks using `celery.chain(query_data.s(...) | transform_data.s(...) | write_csv.s(...) | upload_to_storage.s(...))`. Sets the error callback to update job status to FAILED

### Job State Model (`models.py`)

- `ExportJob` dataclass with fields: `id` (str), `status` (enum: PENDING, RUNNING, SUCCEEDED, FAILED), `progress` (int, 0–100), `result_url` (Optional[str]), `error` (Optional[str]), `created_at` (datetime), `updated_at` (datetime)
- Status transitions: PENDING → RUNNING → SUCCEEDED or FAILED
- No backward transitions allowed (RUNNING → PENDING is invalid)

### Job Store (`store.py`)

- `create_job() -> ExportJob` — Creates a new job with UUID, status=PENDING, progress=0
- `update_job(job_id, **kwargs)` — Updates specified fields and sets `updated_at` to now. Validates status transitions
- `get_job(job_id) -> Optional[ExportJob]` — Returns the job or None
- Must be thread-safe using `threading.Lock` since worker and API may access concurrently

### API Endpoints (`api.py`)

- `POST /exports` — Accepts JSON body `{"table": "users", "filters": {...}, "columns": [...]}`. Creates a job, dispatches `export_report.delay(...)`, returns `{"job_id": "...", "status": "PENDING"}`
- `GET /exports/{job_id}` — Returns the full `ExportJob` as JSON. Returns 404 if job not found

### Retry and Error Handling

- `query_data` uses `@app.task(bind=True, max_retries=3, default_retry_delay=2)` and calls `self.retry(exc=exc, countdown=2 ** self.request.retries)` on `ConnectionError`
- If all retries are exhausted, the job status must be set to FAILED with the error message
- `upload_to_storage` must be idempotent — repeated calls with the same job_id produce the same result without errors

### Expected Functionality

- Calling `POST /exports` with valid params returns a job_id with status PENDING
- After the chain completes, `GET /exports/{job_id}` returns status SUCCEEDED with progress 100 and a result_url
- If `query_data` encounters a `ConnectionError`, it retries up to 3 times with increasing delays (2s, 4s, 8s)
- If all retries fail, `GET /exports/{job_id}` returns status FAILED with the error message
- Calling `upload_to_storage` twice with the same job_id does not fail or duplicate the file

## Acceptance Criteria

- Celery app configures correctly with Redis broker and at-least-once delivery settings
- Task chain (query → transform → write_csv → upload) executes in order with data flowing through
- Each task updates job progress at the expected percentages (25%, 50%, 75%, 100%)
- Retry logic uses exponential backoff on `ConnectionError` up to 3 retries
- Job state transitions validated — no backward transitions allowed
- `upload_to_storage` is idempotent
- API returns correct job status at each stage
- `python -m pytest /workspace/tests/test_python_background_jobs.py -v --tb=short` passes
