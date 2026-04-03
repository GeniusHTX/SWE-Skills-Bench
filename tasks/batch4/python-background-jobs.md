# Task: Implement Asynchronous Report Generation Pipeline in Celery

## Background

The Celery project (https://github.com/celery/celery) is a distributed task queue for Python. A new example application is needed that demonstrates a real-world report generation pipeline: users request a report via an API, the report is processed asynchronously through multiple stages (data fetching, aggregation, rendering, delivery), with job state tracking, idempotency guarantees, and proper error handling at each stage.

## Files to Create/Modify

- `examples/report_pipeline/tasks.py` (create) — Celery task definitions for each pipeline stage with retry configuration and idempotency
- `examples/report_pipeline/models.py` (create) — Job state model with status transitions and result storage
- `examples/report_pipeline/pipeline.py` (create) — Pipeline orchestration using Celery chains and chords
- `examples/report_pipeline/api.py` (create) — FastAPI endpoints for job submission, status polling, and result retrieval
- `examples/report_pipeline/config.py` (create) — Celery app configuration with proper broker/backend settings
- `examples/report_pipeline/test_pipeline.py` (create) — Tests for task idempotency, state transitions, and error handling

## Requirements

### Celery Configuration

- Celery app must configure Redis as both broker and result backend
- Task serializer must be JSON; result serializer must be JSON
- Global task time limit: 600 seconds (hard), 500 seconds (soft)
- Late acknowledgment must be enabled (`task_acks_late=True`)
- Worker prefetch multiplier must be set to 1 to prevent task starvation

### Pipeline Stages (Tasks)

**`fetch_data(job_id, report_type, params)`**
- Queries external data sources based on `report_type` (one of: `"sales"`, `"inventory"`, `"financial"`)
- Stores raw data as a JSON blob in the job record
- Retries up to 3 times on `ConnectionError` and `TimeoutError` with exponential backoff (base 60 seconds)
- Permanent errors (`ValueError`, `KeyError`) must not be retried

**`aggregate_data(job_id)`**
- Reads the raw data from the job record and computes aggregations depending on report type
  - `sales`: total revenue, revenue by region, top 10 products by quantity
  - `inventory`: stock levels by warehouse, items below reorder threshold
  - `financial`: quarterly revenue/expense totals, profit margins
- Stores aggregated results in the job record

**`render_report(job_id, output_format)`**
- Reads aggregated data and renders it into the requested format (`"json"`, `"csv"`, `"html"`)
- Stores the rendered output as a string or binary blob in the job record
- Must handle empty aggregation results gracefully (produce a valid empty report, not an error)

**`deliver_report(job_id, delivery_method)`**
- `delivery_method` is one of: `"store"` (keep in result backend), `"email"` (simulate email delivery), `"webhook"` (simulate HTTP POST)
- For `"email"` and `"webhook"`, retry up to 3 times on delivery failure with 30-second delay
- Updates job status to `"succeeded"` on completion or `"failed"` on permanent failure

### Pipeline Orchestration

- The four stages must be composed into a Celery chain: `fetch_data → aggregate_data → render_report → deliver_report`
- An `on_failure` callback must update the job status to `"failed"` and record the error message
- The pipeline must be triggered by a single `submit_report(report_type, params, output_format, delivery_method)` function that creates the job record and dispatches the chain

### Job State Model

- States: `pending`, `fetching`, `aggregating`, `rendering`, `delivering`, `succeeded`, `failed`
- Each task must update the job status to its corresponding state before starting work
- State transitions must be validated: a job in `"succeeded"` or `"failed"` state cannot transition to any other state
- The job record must store: `id`, `status`, `report_type`, `created_at`, `started_at`, `completed_at`, `raw_data`, `aggregated_data`, `rendered_output`, `error`

### Idempotency

- Each task must check whether its stage's output already exists in the job record before executing; if it does, the task must return immediately without re-executing
- Re-submitting a pipeline for a job ID that already completed must not re-process

### API Endpoints

- `POST /reports` — accepts `report_type`, `params`, `output_format`, `delivery_method`; returns `{"job_id": "...", "status": "pending", "poll_url": "/reports/{job_id}"}`
- `GET /reports/{job_id}` — returns current job status, and the rendered report if status is `"succeeded"`
- `GET /reports/{job_id}` for a nonexistent job returns `404`

### Expected Functionality

- Submitting a sales report request returns a job ID immediately; polling the status URL shows `pending` → `fetching` → `aggregating` → `rendering` → `delivering` → `succeeded`
- If `fetch_data` raises `ConnectionError`, it retries up to 3 times before marking the job as `"failed"`
- Restarting a failed `aggregate_data` task with the same job ID re-uses the already-fetched raw data
- Rendering a report with an empty dataset produces a valid empty report (not an error)
- A `GET /reports/{job_id}` for a completed job returns the rendered report content

## Acceptance Criteria

- Celery app starts and tasks are correctly registered with the configured broker and backend
- The four-stage pipeline executes in the correct order via a Celery chain
- Each task transitions the job state machine correctly and stores intermediate results
- Retries apply only to transient errors with exponential backoff; permanent errors fail immediately
- Idempotent re-execution of any task with already-computed output skips processing
- API returns a job ID on submission and status/result on polling; nonexistent jobs return `404`
- Tests cover successful pipeline completion, retry behavior, idempotency, and state transition validation
