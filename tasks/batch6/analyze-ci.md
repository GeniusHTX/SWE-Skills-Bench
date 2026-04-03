# Task: Build a CI Failure Analysis Tool for GitHub Actions

## Background

A CLI tool is needed that analyzes failed GitHub Actions workflow runs for a given pull request, fetches job logs, identifies root causes, and produces a structured failure report. The tool uses the GitHub API to fetch workflow run data and job logs, then parses log output to categorize failures (test failure, build error, lint violation, timeout, infrastructure issue).

## Files to Create/Modify

- `src/analyze_ci/__init__.py` (create) — Package init
- `src/analyze_ci/cli.py` (create) — CLI entry point: accept PR URL or job URLs, coordinate analysis
- `src/analyze_ci/github_client.py` (create) — GitHub API client: fetch workflow runs, jobs, and logs for a PR
- `src/analyze_ci/log_parser.py` (create) — Parse job logs to extract error messages, test failure names, and stack traces
- `src/analyze_ci/report.py` (create) — Generate structured failure reports in text and JSON formats
- `tests/test_log_parser.py` (create) — Tests for log parsing with sample log fragments
- `tests/test_report.py` (create) — Tests for report generation

## Requirements

### CLI (`src/analyze_ci/cli.py`)

- Usage: `analyze-ci <pr_url> [--format text|json] [--debug]`
- Alternative usage: `analyze-ci <job_url> [<job_url> ...] [--format text|json] [--debug]`
- Parse PR URL format: `https://github.com/{owner}/{repo}/pull/{number}` — extract owner, repo, PR number.
- Parse job URL format: `https://github.com/{owner}/{repo}/actions/runs/{run_id}/job/{job_id}`.
- `--debug` flag: print token usage, API call count, and timing.
- `--format text` (default): human-readable output. `--format json`: machine-readable JSON.
- Authenticate with GitHub token from `GH_TOKEN` env var, or by running `gh auth token` as subprocess fallback.
- Exit code 0 if analysis succeeds (regardless of CI pass/fail), exit code 1 if GitHub API errors occur.

### GitHub Client (`src/analyze_ci/github_client.py`)

- `GitHubClient.__init__(token: str)` — set up authenticated session with `Accept: application/vnd.github.v3+json`.
- `GitHubClient.get_failed_jobs(owner: str, repo: str, pr_number: int) -> list[FailedJob]`:
  1. Fetch PR details to get head SHA: `GET /repos/{owner}/{repo}/pulls/{pr_number}`.
  2. Fetch check suites for the head SHA: `GET /repos/{owner}/{repo}/commits/{sha}/check-suites`.
  3. For each check suite with `conclusion == "failure"`, fetch check runs: `GET /repos/{owner}/{repo}/check-suites/{id}/check-runs`.
  4. For each failed check run, fetch the log: `GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs`.
  5. Return list of `FailedJob(job_id: int, name: str, conclusion: str, started_at: str, completed_at: str, log: str, html_url: str)`.
- `GitHubClient.get_job_log(owner: str, repo: str, job_id: int) -> str` — fetch raw log for a specific job.
- Handle rate limiting: if `x-ratelimit-remaining` is 0, wait until reset time (from `x-ratelimit-reset` header).

### Log Parser (`src/analyze_ci/log_parser.py`)

- `parse_job_log(log: str) -> JobAnalysis`:
  - Extract failure category — one of:
    - `"test_failure"` — detected by patterns: `FAIL`, `FAILED`, `AssertionError`, `Expected ... to equal`, `✕`, `✗`
    - `"build_error"` — detected by: `error TS`, `SyntaxError`, `ModuleNotFoundError`, `cannot find module`, `compilation failed`
    - `"lint_violation"` — detected by: `eslint`, `ruff`, `flake8`, `warning:`, `error:` in lint step context
    - `"timeout"` — detected by: `timed out`, `exceeded the maximum time`, `SIGTERM`, `cancelled`
    - `"infrastructure"` — detected by: `rate limit`, `connection refused`, `ECONNRESET`, `502 Bad Gateway`, `503 Service Unavailable`, `npm ERR! network`
  - Extract failed test names: lines matching patterns like `FAIL src/tests/foo.test.ts`, `FAILED tests/test_bar.py::test_name`, `✕ should do something`.
  - Extract error messages: the first 5 lines containing `Error:`, `error:`, or `Exception:`.
  - Extract stack traces: consecutive indented lines following an error line (up to 20 lines).
  - Return `JobAnalysis(category: str, failed_tests: list[str], error_messages: list[str], stack_traces: list[str], summary: str)`.

- `summarize_failure(analysis: JobAnalysis) -> str`:
  - One-line summary: `"{category}: {N} test(s) failed"` or `"{category}: {first_error_message}"`.

### Report Generator (`src/analyze_ci/report.py`)

- `generate_text_report(pr_url: str, analyses: list[tuple[FailedJob, JobAnalysis]]) -> str`:
  ```
  CI Failure Analysis for https://github.com/org/repo/pull/123

  Found 3 failed jobs:

  1. [test_failure] Unit Tests (Node 20)
     URL: https://github.com/org/repo/actions/runs/xxx/job/yyy
     Duration: 2m 34s
     Failed tests:
       - src/tests/auth.test.ts > should validate JWT token
       - src/tests/auth.test.ts > should reject expired tokens
     Error: Expected 401 to equal 403
     Stack trace:
       at Object.<anonymous> (src/tests/auth.test.ts:42:5)

  2. [build_error] Build API
     ...

  Root cause: 2 test failures in auth.test.ts likely caused by recent changes to JWT validation logic.
  ```

- `generate_json_report(pr_url: str, analyses: list[tuple[FailedJob, JobAnalysis]]) -> str`:
  - JSON with: `{"pr_url": str, "total_failed_jobs": int, "jobs": [{"name": str, "category": str, "url": str, "failed_tests": [...], "error_messages": [...], "summary": str}]}`.

### Expected Functionality

- `analyze-ci https://github.com/facebook/react/pull/12345` → fetches failed jobs for PR #12345, parses logs, prints text report with categorized failures.
- `analyze-ci https://github.com/org/repo/pull/99 --format json` → outputs JSON report.
- A job log containing `FAIL src/App.test.tsx` and `Expected: 200, Received: 500` → categorized as `"test_failure"` with test name and error extracted.
- A job log containing `error TS2304: Cannot find name 'foo'` → categorized as `"build_error"`.
- A job log containing `The job running on runner GitHub Actions 2 has exceeded the maximum execution time` → categorized as `"timeout"`.
- Missing `GH_TOKEN` and `gh auth token` fails → exit 1 with message `"GitHub authentication required: set GH_TOKEN or install gh CLI"`.

## Acceptance Criteria

- CLI accepts both PR URLs and individual job URLs, parsing owner/repo/number or run_id/job_id correctly.
- GitHub client fetches failed jobs for a PR by traversing PR → head SHA → check suites → check runs → logs.
- Log parser correctly categorizes failures into 5 categories: test_failure, build_error, lint_violation, timeout, infrastructure.
- Failed test names are extracted from log lines matching common test runner output patterns (Jest, pytest, Vitest).
- Error messages and stack traces are extracted and limited to prevent unbounded output.
- Text report includes job name, category, URL, duration, failed tests, errors, and a root cause summary line.
- JSON report is valid JSON with all analysis fields.
- Rate limiting is handled gracefully by waiting until the reset time.
