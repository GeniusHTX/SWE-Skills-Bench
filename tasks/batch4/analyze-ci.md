# Task: Build a CI Failure Analyzer Module for Sentry

## Background

The Sentry repository (https://github.com/getsentry/sentry) is an error tracking platform. A new module is needed that fetches GitHub Actions workflow run logs for a given pull request, parses the log output to identify failed jobs and their root causes, classifies failures by category, and produces a structured summary report — enabling developers to quickly understand what went wrong in CI without manually reading log files.

## Files to Create/Modify

- `src/sentry/ci_analysis/__init__.py` (create) — Package init
- `src/sentry/ci_analysis/log_fetcher.py` (create) — Fetches workflow run logs from GitHub Actions API
- `src/sentry/ci_analysis/log_parser.py` (create) — Parses raw log text to extract error messages, failed test names, and stack traces
- `src/sentry/ci_analysis/failure_classifier.py` (create) — Classifies failures into categories (test failure, build error, timeout, flaky, infrastructure)
- `src/sentry/ci_analysis/reporter.py` (create) — Generates structured failure summary reports
- `tests/sentry/ci_analysis/test_ci_analysis.py` (create) — Tests for parsing, classification, and reporting

## Requirements

### Log Fetcher

- `LogFetcher` class accepting: `github_token` (str), `repo_owner` (str), `repo_name` (str)
- `fetch_failed_jobs(pr_number: int) -> list[dict]` — uses the GitHub REST API to list workflow runs for the PR's head SHA, then fetches logs for failed jobs; returns `[{"job_id": int, "job_name": str, "status": str, "conclusion": str, "log_text": str, "url": str}]`
- `fetch_job_log(job_id: int) -> str` — fetches the raw log text for a single job via `GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs`
- Must handle HTTP 404 (job not found) and 403 (rate limited) by returning an appropriate error dict instead of raising
- Must set a timeout of 30 seconds per request

### Log Parser

- `LogParser` class (stateless, no constructor parameters)
- `parse(log_text: str) -> ParseResult` — extracts structured information from raw log output
- `ParseResult` fields:
  - `errors`: list of `{"message": str, "line_number": int}` for lines matching error patterns
  - `failed_tests`: list of `{"test_name": str, "error_message": str, "file_path": str}` extracted from test runner output (supports pytest, jest, and JUnit formats)
  - `stack_traces`: list of multi-line stack trace strings
  - `exit_code`: int or None — extracted from "Process completed with exit code N" pattern
  - `duration_seconds`: float or None — extracted from timing lines
- Error pattern matching must detect: lines starting with `ERROR`, `FAILED`, `FATAL`, `error:`, `Error:`, and ANSI-colored error markers
- pytest-specific parsing: match `FAILED test_module::TestClass::test_name` patterns and extract the assertion error
- jest-specific parsing: match `FAIL src/path/to/test.js` and `● TestSuite › test name` patterns

### Failure Classifier

- `FailureClassifier` class (stateless)
- `classify(parse_result: ParseResult) -> FailureClassification` with fields:
  - `category`: one of `"test_failure"`, `"build_error"`, `"lint_error"`, `"timeout"`, `"infrastructure"`, `"dependency"`, `"unknown"`
  - `confidence`: float 0.0–1.0
  - `reasoning`: str explaining the classification
- Classification rules:
  - `"test_failure"`: `failed_tests` list is non-empty
  - `"build_error"`: errors contain compilation keywords (`"compile"`, `"build failed"`, `"syntax error"`, `"cannot find module"`)
  - `"lint_error"`: errors contain lint keywords (`"eslint"`, `"pylint"`, `"flake8"`, `"formatting"`)
  - `"timeout"`: exit code is 124 or log contains `"timed out"`, `"timeout"`, `"exceeded time limit"`
  - `"infrastructure"`: log contains `"out of memory"`, `"disk full"`, `"connection refused"`, `"runner failed"`
  - `"dependency"`: log contains `"package not found"`, `"dependency resolution"`, `"version conflict"`, `"ModuleNotFoundError"`
  - `"unknown"`: none of the above match
- When multiple categories match, prefer the one with the highest confidence (test_failure > build_error > dependency > lint_error > timeout > infrastructure > unknown)

### Reporter

- `FailureReporter` class
- `generate_report(jobs: list[dict], parse_results: list[ParseResult], classifications: list[FailureClassification]) -> dict` — returns:
  - `"summary"`: string with one-line overview (e.g., "3 of 5 jobs failed: 2 test failures, 1 build error")
  - `"failed_jobs"`: list of `{"job_name": str, "category": str, "key_errors": list[str], "failed_tests": list[str]}`
  - `"root_cause"`: string with the most likely root cause across all failures
  - `"total_jobs"`, `"failed_count"`, `"categories"` (dict of category → count)

### Expected Functionality

- Parsing a pytest log with `FAILED tests/test_auth.py::TestLogin::test_invalid_token - AssertionError: 401 != 200` extracts the test name and error
- Parsing a jest log with `FAIL src/__tests__/auth.test.js` and `● Auth › should reject invalid tokens` extracts both patterns
- A log containing "Process completed with exit code 124" classifies as `"timeout"`
- A log with ModuleNotFoundError classifies as `"dependency"`
- A report for 5 jobs with 2 test failures and 1 build error produces a summary string and categorized breakdown

## Acceptance Criteria

- Log fetcher correctly calls GitHub Actions API endpoints with proper authentication and timeout handling
- Log parser extracts errors, failed tests, stack traces, and exit codes from pytest, jest, and generic log formats
- Failure classifier assigns the correct category based on log content with appropriate confidence scores
- Reporter produces a structured summary with per-job breakdowns and an overall root cause assessment
- Edge cases (empty logs, no failed jobs, unparseable output) are handled gracefully without raising
- Tests verify parsing accuracy for each supported log format, classification rules, and report generation
