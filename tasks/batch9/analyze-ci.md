# Task: Build a CI Failure Analyzer for Sentry's GitHub Actions Workflows

## Background

Sentry (https://github.com/getsentry/sentry) has complex CI pipelines with GitHub Actions. A new Python tool is needed that fetches CI workflow run data from the GitHub API, parses build/test logs to identify root causes of failures, classifies failure types (flaky test, dependency error, build error, timeout, infrastructure), and generates structured failure reports with actionable remediation suggestions.

## Files to Create/Modify

- `tools/ci_analyzer/analyzer.py` (create) — `CIFailureAnalyzer` class that fetches workflow run and job data from GitHub API, downloads logs, and orchestrates analysis
- `tools/ci_analyzer/log_parser.py` (create) — `LogParser` class with methods to extract error messages, failed test names, stack traces, and timing information from CI log output
- `tools/ci_analyzer/classifier.py` (create) — `FailureClassifier` class that categorizes failures into types based on error patterns and provides remediation suggestions
- `tools/ci_analyzer/report.py` (create) — `FailureReport` class that formats analysis results as Markdown, JSON, and GitHub comment body
- `tools/ci_analyzer/cli.py` (create) — CLI entry point accepting PR URL or workflow run URL, outputting analysis results
- `tests/test_ci_analyzer.py` (create) — Tests with sample log fixtures covering all failure types

## Requirements

### Log Parser (`log_parser.py`)

- Class `LogParser` with method `parse(log_content: str) -> ParsedLog`:
- `ParsedLog` dataclass: `errors` (list[ErrorInfo]), `failed_tests` (list[FailedTest]), `timing` (dict), `exit_code` (Optional[int])
- `ErrorInfo`: `message` (str), `line_number` (int), `context` (str, 3 lines before and after), `category` (str)
- `FailedTest`: `name` (str), `file_path` (Optional[str]), `error_message` (str), `duration_seconds` (Optional[float])
- Error extraction patterns (regex-based):
  - Python tracebacks: match `Traceback (most recent call last):` through the final error line
  - pytest failures: match `FAILED tests/` patterns, extract test name and assertion message
  - npm/yarn errors: match `error TS\d+:`, `ERR!`, `SyntaxError`
  - Docker build errors: match `ERROR [` lines
  - Timeout markers: match `The job running on runner .* has exceeded the maximum execution time` or `##[error]The operation was canceled`
  - Exit codes: match `Process completed with exit code (\d+)`
- Method `extract_timing(log_content: str) -> dict` — Extracts step durations from `##[group]` / `##[endgroup]` markers and `::set-output` timing annotations
- Must handle logs up to 10MB without excessive memory usage (stream-process line by line)

### Failure Classifier (`classifier.py`)

- Class `FailureClassifier` with method `classify(parsed_log: ParsedLog) -> Classification`:
- `Classification` dataclass: `failure_type` (enum: FLAKY_TEST, DEPENDENCY_ERROR, BUILD_ERROR, TEST_FAILURE, TIMEOUT, INFRASTRUCTURE, UNKNOWN), `confidence` (float 0–1), `root_cause` (str), `remediation` (str)
- Classification rules:
  - `FLAKY_TEST`: test failed with no code changes in the PR diff (detected by test name being in a known flaky list, or test failure message contains "timeout", "connection refused", "resource temporarily unavailable")
  - `DEPENDENCY_ERROR`: log contains "Could not resolve", "No matching distribution", "npm ERR! 404", "ENOENT", or pip/yarn/npm install failures
  - `BUILD_ERROR`: log contains compile errors (TypeScript TS\d+, Python SyntaxError, gcc/clang error), "Build failed"
  - `TEST_FAILURE`: pytest FAILED lines with assertion errors, non-flaky test failures
  - `TIMEOUT`: "exceeded the maximum execution time" or "operation was canceled" with no other errors
  - `INFRASTRUCTURE`: "No space left on device", "runner is offline", "out of memory", GitHub API rate limits
  - `UNKNOWN`: none of the above patterns match
- Each failure type maps to a remediation string (e.g., DEPENDENCY_ERROR → "Check dependency version constraints and network access. Try clearing the pip/npm cache.")
- Confidence is 0.9 for strong pattern matches, 0.7 for partial matches, 0.5 for heuristic classification

### CI Failure Analyzer (`analyzer.py`)

- Class `CIFailureAnalyzer` accepts: `github_token` (str), `http_client` (optional, for testing)
- Method `analyze_pr(pr_url: str) -> list[JobAnalysis]`:
  - Parse owner, repo, PR number from the URL
  - Fetch all workflow runs for the PR's head SHA using GitHub API: `GET /repos/{owner}/{repo}/actions/runs?head_sha={sha}`
  - For each failed run, fetch jobs: `GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs`
  - For each failed job, download logs: `GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs`
  - Parse and classify each job's log
  - Return list of `JobAnalysis(job_name, job_url, classification, parsed_log)`
- Method `analyze_job(job_url: str) -> JobAnalysis` — Analyze a single job URL directly
- All GitHub API requests must include `Authorization: Bearer {token}` header
- Handle rate limiting: if response status is 403 with rate limit headers, wait and retry once

### Report (`report.py`)

- Method `to_markdown(analyses: list[JobAnalysis]) -> str` — Generates Markdown with:
  - Summary table: job name, failure type, confidence, root cause (one row per job)
  - Detailed sections per job with error messages, failed tests, and remediation
  - Collapsible `<details>` blocks for full error context
- Method `to_json(analyses: list[JobAnalysis]) -> str` — JSON-serialized analysis results
- Method `to_github_comment(analyses: list[JobAnalysis]) -> str` — GitHub-flavored Markdown optimized for PR comments, with emoji status indicators

### Expected Functionality

- Analyzing a log containing `FAILED tests/test_api.py::test_create_user - AssertionError: 404 != 201` classifies as TEST_FAILURE with the test name extracted
- A log with `npm ERR! 404 '@sentry/webpack-plugin@99.0.0' is not in this registry` classifies as DEPENDENCY_ERROR
- A log ending with `The operation was canceled` and no test failures classifies as TIMEOUT
- The Markdown report for 3 failed jobs contains a summary table with 3 rows and 3 detail sections

## Acceptance Criteria

- Log parser correctly extracts Python tracebacks, pytest failures, npm errors, and timeouts using regex patterns
- Failure classifier assigns correct types with appropriate confidence for all 7 categories
- CI analyzer correctly constructs GitHub API URLs from PR URLs and handles authentication
- Rate limiting is handled with a single retry after waiting
- Report generator produces valid Markdown with summary table and collapsible detail sections
- All log processing handles large inputs (10MB) without excessive memory use
- `python -m pytest /workspace/tests/test_analyze_ci.py -v --tb=short` passes
