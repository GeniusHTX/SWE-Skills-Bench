# Task: Implement a Scheduled Report Generation Pipeline with Celery

## Background

Celery (https://github.com/celery/celery) is a distributed task queue for Python. The project's `examples/` directory provides sample applications demonstrating common Celery patterns. A new end-to-end example is needed: a scheduled report generation pipeline that accepts report requests, processes them asynchronously through multiple stages (data collection, aggregation, formatting), tracks job state, and supports cancellation. This example must demonstrate production-grade task patterns including idempotency, state management, error handling, and task chaining.

## Files to Create/Modify

- `examples/report_pipeline/app.py` (create) — Celery application instance with broker/backend configuration
- `examples/report_pipeline/tasks.py` (create) — Task definitions for `collect_data`, `aggregate_data`, `format_report`, and `send_report` stages
- `examples/report_pipeline/models.py` (create) — `ReportJob` dataclass with state machine (PENDING → COLLECTING → AGGREGATING → FORMATTING → SENDING → COMPLETED / FAILED / CANCELLED)
- `examples/report_pipeline/store.py` (create) — Simple JSON file-backed job store for persisting `ReportJob` state
- `examples/report_pipeline/api.py` (create) — Flask/FastAPI endpoints: `POST /reports` (create job), `GET /reports/{id}` (poll status), `POST /reports/{id}/cancel` (cancel job)
- `examples/report_pipeline/README.md` (create) — Usage instructions

## Requirements

### Task Pipeline Stages

- `collect_data(job_id: str, data_source: str, date_range: dict) -> dict` — Simulates data collection by reading from a configurable source; returns a dictionary of raw data keyed by metric name
- `aggregate_data(job_id: str, raw_data: dict, aggregation: str) -> dict` — Computes aggregations (sum, average, min, max, count) over the raw data; `aggregation` must be one of `["sum", "average", "min", "max", "count"]`; invalid values raise `ValueError`
- `format_report(job_id: str, aggregated_data: dict, format: str) -> str` — Converts aggregated data to the requested format: `"json"`, `"csv"`, or `"text"`; returns the formatted string
- `send_report(job_id: str, formatted_report: str, destination: str) -> dict` — Simulates sending the report to a destination (writes to a file path); returns `{"delivered": True, "destination": destination, "size_bytes": len(formatted_report)}`
- The four tasks must be chained together using Celery's `chain` primitive so that the output of one stage feeds into the next

### Job State Machine

- `ReportJob` must have fields: `id` (str), `status` (enum), `created_at` (datetime), `updated_at` (datetime), `stages_completed` (list[str]), `result` (optional dict), `error` (optional str)
- Valid status transitions: `PENDING → COLLECTING → AGGREGATING → FORMATTING → SENDING → COMPLETED`; any stage can transition to `FAILED` or `CANCELLED`
- Each task must update the job status at the start and end of its execution
- A job in `CANCELLED` status must cause subsequent pipeline stages to skip execution and return immediately

### Idempotency

- Each task must check for duplicate execution by verifying the current job status before proceeding; if the stage has already been completed (present in `stages_completed`), the task must return the cached result without re-executing
- The job store must use file-locking or atomic writes to prevent corruption under concurrent access

### Error Handling and Retries

- `collect_data` must retry up to 3 times on `ConnectionError` or `TimeoutError` with exponential backoff starting at 5 seconds
- `aggregate_data` must not retry on `ValueError` (invalid aggregation type) — this is a permanent failure that transitions the job to `FAILED`
- `format_report` must retry up to 2 times on `OSError`
- `send_report` must retry up to 3 times on `OSError` or `ConnectionError`
- When all retries are exhausted, the job must transition to `FAILED` with the exception message stored in the `error` field

### Cancellation

- `POST /reports/{id}/cancel` sets the job status to `CANCELLED` and revokes the Celery task chain
- Each task must check the job status at entry; if the job is `CANCELLED`, the task must return immediately without processing and without changing the status

### API Endpoints

- `POST /reports` accepts `{"data_source": str, "date_range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}, "aggregation": str, "format": str, "destination": str}`; returns `{"job_id": str, "status": "PENDING", "poll_url": "/reports/{id}"}` with HTTP 202
- `GET /reports/{id}` returns the full `ReportJob` as JSON with HTTP 200, or HTTP 404 if not found
- `POST /reports/{id}/cancel` returns HTTP 200 with updated status, HTTP 404 if not found, or HTTP 400 if the job is already in a terminal state (`COMPLETED`, `FAILED`, `CANCELLED`)
- `date_range.start` must be before `date_range.end`; violation returns HTTP 400
- `data_source` must not be empty; `format` must be one of `["json", "csv", "text"]`; violations return HTTP 400

## Expected Functionality

- `POST /reports` with valid parameters returns HTTP 202 and a job ID; subsequent `GET /reports/{id}` shows status progressing through `COLLECTING → AGGREGATING → FORMATTING → SENDING → COMPLETED`
- A report with `aggregation: "average"` and `format: "csv"` produces a CSV-formatted string with averaged metric values
- Posting `cancel` while a job is in `AGGREGATING` status causes subsequent `format_report` and `send_report` stages to be skipped
- Re-submitting `collect_data` for a job that already completed collection returns the cached result without re-executing
- A `collect_data` task encountering a `ConnectionError` retries up to 3 times; if all fail, the job transitions to `FAILED`
- `POST /reports` with `date_range.start > date_range.end` returns HTTP 400

## Acceptance Criteria

- A four-stage task pipeline (collect → aggregate → format → send) executes end-to-end using Celery's `chain` primitive, with each stage updating the job state
- Jobs track state transitions with `status`, `stages_completed`, and timestamps; invalid transitions are prevented
- Duplicate task execution for an already-completed stage returns cached results without re-processing
- Transient errors trigger automatic retries with exponential backoff; permanent errors immediately transition the job to `FAILED`
- Cancellation via the API endpoint prevents subsequent pipeline stages from executing
- API validates input (date range ordering, format values, required fields) and returns appropriate HTTP status codes
- The job store handles concurrent access without data corruption
