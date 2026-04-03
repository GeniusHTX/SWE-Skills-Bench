# Task: Implement a CI Failure Analyzer for GitHub Actions Workflows

## Background

Sentry's codebase uses GitHub Actions for CI. When builds fail, developers need to quickly understand root causes from workflow logs. A new Python module is needed that fetches failed GitHub Actions job logs for a given pull request, parses them to extract structured failure information, and classifies failures into actionable categories (test failure, lint error, build error, timeout, infrastructure flake).

## Files to Create/Modify

- `src/sentry/utils/ci_analyzer/__init__.py` (new) — Package init exporting the public API
- `src/sentry/utils/ci_analyzer/fetcher.py` (new) — Module to fetch failed workflow run and job data from the GitHub API for a given PR
- `src/sentry/utils/ci_analyzer/parser.py` (new) — Log parser that extracts failure signals from raw job logs
- `src/sentry/utils/ci_analyzer/classifier.py` (new) — Failure classifier that categorizes parsed failures into known categories with confidence scores
- `src/sentry/utils/ci_analyzer/models.py` (new) — Data classes for PR info, job failure records, parsed failure signals, and classification results
- `src/sentry/utils/ci_analyzer/cli.py` (new) — CLI entry point that accepts a PR URL and outputs a structured failure report

## Requirements

### PR and Job Fetching

- Given a GitHub PR URL (e.g., `https://github.com/getsentry/sentry/pull/12345`), extract the owner, repo, and PR number
- Fetch the list of workflow runs associated with the PR's head SHA via the GitHub API (`GET /repos/{owner}/{repo}/actions/runs?head_sha={sha}`)
- For each failed workflow run, fetch the list of jobs and identify those with `conclusion: "failure"`
- Extract job name, step name, started_at, completed_at, and failure log URL for each failed job
- If the PR URL format is invalid, raise a `ValueError` with the message "Invalid PR URL format: expected https://github.com/{owner}/{repo}/pull/{number}"
- If the GitHub API returns 404 for the PR, raise a `ValueError` with "PR not found: {url}"

### Log Parsing

- Download raw logs for each failed job step
- Extract failure signals: error messages (lines matching common patterns like `FAILED`, `Error:`, `AssertionError`, `TIMEOUT`, `exit code`), stack traces (consecutive indented lines following a known error pattern), and timing data (step duration)
- For each failure signal, record: the originating job name, step name, line number range, extracted error text (max 500 characters), and whether a stack trace was captured
- If the log is empty or cannot be downloaded, record a signal with category `unknown` and error text "Log unavailable"

### Failure Classification

- Classify each parsed failure signal into one of: `test_failure`, `lint_error`, `build_error`, `timeout`, `infra_flake`, `unknown`
- Classification rules:
  - `test_failure`: error text contains "FAILED", "AssertionError", "pytest", "unittest", or "test" in the step name
  - `lint_error`: step name contains "lint" or "format", or error text contains "flake8", "eslint", "mypy", "ruff"
  - `build_error`: step name contains "build" or "compile", or error text contains "ModuleNotFoundError", "ImportError", "SyntaxError", "compilation failed"
  - `timeout`: error text contains "TIMEOUT", "timed out", or step duration exceeds 30 minutes
  - `infra_flake`: error text contains "rate limit", "503", "connection reset", "socket timeout", "ECONNREFUSED"
  - `unknown`: no rule matches
- Each classification must include a confidence score: 1.0 if the step name matches the category, 0.8 if only error text matches, 0.5 for `unknown`

### Report Output

- The CLI outputs a JSON report with: `pr_url`, `head_sha`, `analyzed_at` (ISO 8601), `total_failed_jobs`, `failures` (array of classified failure records), `summary` (count per category)
- Each failure record contains: `job_name`, `step_name`, `category`, `confidence`, `error_text`, `has_stacktrace`, `line_range`
- With `--format text` flag, output a human-readable summary table with columns: JOB, STEP, CATEGORY, CONFIDENCE, ERROR (truncated to 80 chars)
- The summary section in JSON counts each category (e.g., `{"test_failure": 3, "build_error": 1, "infra_flake": 0, ...}`)

### Expected Functionality

- PR with 2 failed jobs: one with a pytest AssertionError in step "Run tests" and one with a ModuleNotFoundError in step "Build wheel" → report contains one `test_failure` (confidence 1.0) and one `build_error` (confidence 1.0)
- PR with a job that timed out after 45 minutes in step "Integration tests" → classified as `timeout` (confidence 0.8)
- PR with a job whose log contains "503 Service Unavailable" in step "Deploy preview" → classified as `infra_flake` (confidence 0.8)
- PR with a job that has no downloadable logs → failure record with category `unknown`, error text "Log unavailable", confidence 0.5
- Invalid PR URL "not-a-url" → `ValueError` with the expected message
- `--format text` output shows a readable table with truncated error messages

## Acceptance Criteria

- The fetcher correctly parses owner, repo, and PR number from valid GitHub PR URLs and raises `ValueError` for invalid URLs
- The parser extracts error messages, stack traces, and timing data from raw CI logs
- The classifier maps each failure signal to the correct category and confidence score according to the classification rules
- The JSON report includes all required fields, correct failure counts per category in the summary, and ISO 8601 timestamp
- Text output mode produces a formatted table with all failure records
- Jobs with unavailable logs are included in the report with category `unknown`
- All modules are importable and unit tests pass via `python -m pytest /workspace/tests/test_analyze_ci.py -v`
