# Task: Build a CI Failure Analysis Report Generator for Sentry

## Background

Sentry (https://github.com/getsentry/sentry) has a complex CI pipeline with hundreds of GitHub Actions jobs. When CI fails, developers spend significant time scrolling through log output to find the root cause. This task requires building a Python script that ingests a GitHub Actions log file, extracts structured failure information, classifies the error type, and outputs a concise diagnostic report.

## Files to Create/Modify

- `scripts/ci_failure_analyzer.py` (create) — Main analysis script: reads a CI log file, parses job/step structure, extracts errors, classifies failures, and outputs a JSON diagnostic report.
- `scripts/ci_failure_types.py` (create) — Defines failure type taxonomy (test failure, build error, lint error, timeout, dependency resolution, infrastructure flake) with classification rules.
- `scripts/ci_report_formatter.py` (create) — Formats the JSON diagnostic report into a human-readable Markdown summary.
- `tests/test_ci_failure_analyzer.py` (create) — Unit tests covering parsing, classification, and report generation with sample log snippets.

## Requirements

### Log Parsing

- Parse GitHub Actions log format: identify job names, step names, timestamps, exit codes, and annotation lines (`::error::`, `::warning::`).
- Extract the first 10 error lines and their surrounding context (5 lines before, 5 lines after) from each failed step.
- Identify the specific failed step within each failed job (a step with non-zero exit code or `::error::` annotation).

### Failure Classification

- Classify each failure into one of these categories:
  - `test_failure` — Contains patterns like `FAILED`, `AssertionError`, `pytest` failure markers, or `unittest` failure output.
  - `build_error` — Contains compiler errors, `ModuleNotFoundError`, `ImportError`, or build tool failure messages.
  - `lint_error` — Contains linter output patterns (`flake8`, `mypy`, `eslint`, `black --check`).
  - `timeout` — Step exceeded time limit or contains `TimeoutError`, `timed out`.
  - `dependency_error` — Contains `pip install` failures, `npm ERR!`, `ResolutionImpossible`, or lock-file conflicts.
  - `infra_flake` — Contains `rate limit`, `connection reset`, `503`, `ECONNREFUSED`, or Docker pull failures.
- If a failure matches multiple categories, assign the most specific one (e.g., `test_failure` takes precedence over `build_error`).

### Report Output (JSON)

- `summary`: One-sentence description of the overall failure.
- `total_failed_jobs`: Integer count.
- `failures`: Array of objects, each with `job_name`, `step_name`, `failure_type`, `error_message` (first error line), `context` (surrounding lines), `exit_code`.
- `suggested_action`: A brief suggested next step for each failure type (e.g., "Re-run the job" for `infra_flake`, "Fix the failing test assertion" for `test_failure`).

### Markdown Formatter

- Convert the JSON report into a Markdown document with: a summary header, a table of failed jobs, and collapsible detail sections for each failure.

### Expected Functionality

- A log containing `FAILED tests/test_foo.py::test_bar - AssertionError: expected 1, got 2` in step "Run pytest" → classified as `test_failure`, error message extracted, context captured.
- A log containing `ERROR: Could not find a version that satisfies the requirement nonexistent-package==1.0` → classified as `dependency_error`.
- A log containing `Error: Process completed with exit code 1` but only after `::error::Connection reset by peer` → classified as `infra_flake`.
- Empty or malformed log input → returns a report with `total_failed_jobs: 0` and a summary indicating no failures detected.

## Acceptance Criteria

- The analyzer correctly parses job/step structure and exit codes from GitHub Actions log format.
- Failure classification assigns the correct category for test failures, build errors, lint errors, timeouts, dependency errors, and infrastructure flakes.
- The JSON report includes all required fields (`summary`, `total_failed_jobs`, `failures` array with per-failure details).
- The Markdown formatter produces a readable report with a summary table and per-failure detail sections.
- Unit tests pass, covering at least one sample log for each of the six failure categories and the empty-input edge case.
