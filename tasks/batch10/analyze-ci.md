# Task: Implement GitHub Actions CI Failure Analyzer CLI for Sentry

## Background

The Sentry project (`getsentry/sentry`) has a complex CI pipeline defined in `.github/workflows/` with dozens of GitHub Actions jobs. When a pull request fails CI, developers spend significant time navigating the Actions UI to find the root cause across multiple failed jobs. A new CLI tool is needed under `src/sentry/utils/ci/` that takes a PR URL or job URL, fetches failed job logs via the GitHub API, parses the logs to extract error messages, failed test names, and stack traces, and produces a concise failure summary.

## Files to Create/Modify

- `src/sentry/utils/ci/analyzer.py` (new) — Core analyzer class that accepts a GitHub PR URL or job URL, resolves the run and failed jobs, downloads logs, and orchestrates parsing
- `src/sentry/utils/ci/github_client.py` (new) — GitHub API client that authenticates via `GH_TOKEN` env var or `gh auth token` subprocess, fetches workflow runs for a PR, lists jobs per run, and downloads job log content
- `src/sentry/utils/ci/log_parser.py` (new) — Log parser that extracts error lines, Python/JavaScript stack traces, failed pytest test names, failed Jest test names, and linting errors from raw GitHub Actions log output
- `src/sentry/utils/ci/formatter.py` (new) — Output formatter that takes parsed failure data and produces a structured Markdown summary with sections for root cause, error messages, failed tests, and relevant log snippets
- `src/sentry/utils/ci/cli.py` (new) — CLI entry point using `argparse` that accepts positional URL arguments (PR or job URLs), a `--debug` flag for token/cost info, and a `--format` option (`text` or `json`)
- `tests/sentry/utils/ci/test_log_parser.py` (new) — Unit tests for log parsing across different failure patterns
- `tests/sentry/utils/ci/test_analyzer.py` (new) — Unit tests for the analyzer with mocked GitHub API responses
- `tests/sentry/utils/ci/test_formatter.py` (new) — Unit tests for output formatting

## Requirements

### GitHub Client (`github_client.py`)

- Class `GitHubActionsClient` with `__init__(self, token: str | None = None)`
- If `token` is `None`, attempt to read `GH_TOKEN` environment variable; if that's unset, attempt `subprocess.run(["gh", "auth", "token"])` to get it; raise `RuntimeError` with a descriptive message if all methods fail
- Method `get_workflow_runs(owner: str, repo: str, pr_number: int) -> list[dict]` — call `GET /repos/{owner}/{repo}/actions/runs?event=pull_request` and filter to runs associated with the given PR number
- Method `get_failed_jobs(owner: str, repo: str, run_id: int) -> list[dict]` — call `GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs` and return only jobs with `conclusion == "failure"`
- Method `download_job_log(owner: str, repo: str, job_id: int) -> str` — call `GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs` and return the raw log text
- Method `parse_url(url: str) -> dict` — parse a GitHub URL and return `{"type": "pr"|"job", "owner": str, "repo": str, "pr_number": int|None, "run_id": int|None, "job_id": int|None}`; raise `ValueError` for URLs that don't match expected patterns (`github.com/{owner}/{repo}/pull/{number}` or `github.com/{owner}/{repo}/actions/runs/{run_id}/job/{job_id}`)
- All HTTP requests must set a `User-Agent` header and `Authorization: Bearer {token}` header
- Raise `requests.HTTPError` on non-2xx responses with the status code in the message

### Log Parser (`log_parser.py`)

- Function `parse_log(raw_log: str) -> dict` returning:
  - `"errors": list[str]` — lines matching patterns like `Error:`, `FAILED`, `FATAL`, `Exception:`, `error:` (case-insensitive), deduplicated
  - `"stack_traces": list[str]` — contiguous blocks of lines that look like Python tracebacks (`Traceback (most recent call last):` through the exception line) or JavaScript stack traces (`at Function.<anonymous>` patterns)
  - `"failed_tests": list[str]` — test identifiers extracted from pytest output (`FAILED tests/path/test_file.py::TestClass::test_method`) and Jest output (`FAIL src/path/test_file.test.js` / `✕ test name`)
  - `"lint_errors": list[str]` — lines matching flake8 (`file.py:line:col: E123 message`), ruff, or eslint output patterns
  - `"annotations": list[str]` — GitHub Actions `::error::` annotation lines
- Function `extract_relevant_context(raw_log: str, error_line: str, context_lines: int = 5) -> str` — return the error line plus `context_lines` lines above and below from the raw log
- Handle ANSI escape codes: strip all `\x1b[...m` sequences before parsing
- Handle GitHub Actions timestamp prefixes: strip `2024-01-15T10:30:00.1234567Z ` prefixes from lines before pattern matching

### Formatter (`formatter.py`)

- Function `format_summary(analysis: dict, format: str = "text") -> str`
- For `format="text"` return a Markdown document with:
  - `## CI Failure Summary` header
  - `### Root Cause` — the first error or most common error pattern
  - `### Failed Tests` — bulleted list of test names (or "No test failures detected")
  - `### Error Messages` — numbered list of unique error messages (max 10)
  - `### Stack Traces` — fenced code blocks for each trace (max 3, truncated to 30 lines each)
  - `### Relevant Log Snippets` — context around each error (max 5 snippets)
- For `format="json"` return a JSON string with keys `root_cause`, `failed_tests`, `errors`, `stack_traces`, `lint_errors`
- Raise `ValueError` if `format` is not `"text"` or `"json"`

### CLI (`cli.py`)

- Accept one or more positional URL arguments
- Flag `--debug` prints the GitHub token source (not the token itself) and request count
- Flag `--format` accepts `text` (default) or `json`
- For a PR URL: fetch all workflow runs for that PR, find all failed jobs across all runs, analyze each
- For a job URL: analyze that single job directly
- Exit code `0` if analysis succeeds (even if CI has failures); exit code `1` if the tool itself encounters an error (bad URL, auth failure, API error)
- Print output to stdout

### Expected Functionality

- Given a log containing `Traceback (most recent call last):\n  File "test.py", line 10\nValueError: invalid input` → `stack_traces` contains that full traceback block
- Given a log containing `FAILED tests/sentry/api/test_organization.py::TestOrgAPI::test_create - AssertionError` → `failed_tests` contains `tests/sentry/api/test_organization.py::TestOrgAPI::test_create`
- Given a log containing `FAIL src/sentry/static/app/components/__tests__/button.test.tsx` → `failed_tests` contains that path
- Given a log with `::error::Process completed with exit code 1` → `annotations` contains that line
- Given a log with `src/sentry/models/user.py:45:1: E302 expected 2 blank lines` → `lint_errors` contains that line
- Given a log with ANSI codes like `\x1b[31mError: something broke\x1b[0m` → parsed as `Error: something broke`
- `parse_url("https://github.com/getsentry/sentry/pull/12345")` → `{"type": "pr", "owner": "getsentry", "repo": "sentry", "pr_number": 12345}`
- `parse_url("https://github.com/getsentry/sentry/actions/runs/9876/job/5432")` → `{"type": "job", "owner": "getsentry", "repo": "sentry", "run_id": 9876, "job_id": 5432}`
- `parse_url("https://example.com/not-github")` → raises `ValueError`
- CLI with `--format json` → output is valid JSON parseable by `json.loads`
- A PR with 3 failed jobs → summary includes failures from all 3 jobs
- GitHub token not found anywhere → `RuntimeError` with message mentioning `GH_TOKEN` and `gh auth token`

## Acceptance Criteria

- `python -m pytest tests/sentry/utils/ci/test_log_parser.py -v --timeout=120` passes all tests
- `python -m pytest tests/sentry/utils/ci/test_analyzer.py -v --timeout=120` passes all tests
- `python -m pytest tests/sentry/utils/ci/test_formatter.py -v --timeout=120` passes all tests
- Log parser correctly extracts Python tracebacks, pytest failures, Jest failures, lint errors, and GitHub Actions annotations from real-world log samples
- ANSI escape codes and timestamp prefixes are stripped before parsing
- GitHub client correctly resolves both PR URLs and job URLs
- Formatter produces valid Markdown for text mode and valid JSON for json mode
- CLI returns exit code `0` on successful analysis and `1` on tool errors
- All GitHub API calls include proper authentication and User-Agent headers
