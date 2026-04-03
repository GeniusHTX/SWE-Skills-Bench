# Task: Implement a CI Build Failure Analyzer Service in Sentry

## Background

Sentry (https://github.com/getsentry/sentry) is an error monitoring platform. The task is to implement a CI build failure analyzer service that ingests GitHub Actions job logs, classifies failure types (test failure, build error, timeout, infrastructure), extracts relevant error messages and stack traces, and provides structured failure reports through a REST API endpoint.

## Files to Create/Modify

- `src/sentry/ci_analysis/models.py` (create) — Django models for storing CI build failure records and analysis results
- `src/sentry/ci_analysis/analyzer.py` (create) — `CIFailureAnalyzer` class that parses GitHub Actions logs, classifies failures, and extracts root cause information
- `src/sentry/ci_analysis/api.py` (create) — DRF API endpoint for submitting CI logs and retrieving analysis results
- `src/sentry/ci_analysis/__init__.py` (create) — Package init
- `tests/sentry/ci_analysis/test_analyzer.py` (create) — Unit tests for the failure analyzer
- `tests/sentry/ci_analysis/test_api.py` (create) — Unit tests for the API endpoint
- `tests/sentry/ci_analysis/__init__.py` (create) — Package init

## Requirements

### Models (`models.py`)

#### `CIBuildFailure`
- `id` — `BigAutoField` primary key
- `organization` — `ForeignKey` to `sentry.models.Organization`
- `repository` — `CharField(max_length=512)` (e.g., `"getsentry/sentry"`)
- `workflow_name` — `CharField(max_length=256)`
- `job_name` — `CharField(max_length=256)`
- `run_id` — `BigIntegerField` (GitHub Actions run ID)
- `job_id` — `BigIntegerField` (GitHub Actions job ID)
- `failure_type` — `CharField` with choices: `"test_failure"`, `"build_error"`, `"timeout"`, `"infrastructure"`, `"dependency"`, `"unknown"`
- `status` — `CharField` with choices: `"pending"`, `"analyzed"`, `"error"`
- `raw_log` — `TextField` (the raw CI log text)
- `analysis_result` — `JSONField(null=True)` (structured analysis output)
- `created_at` — `DateTimeField(auto_now_add=True)`
- `analyzed_at` — `DateTimeField(null=True)`
- Meta: indexes on `(organization, repository)`, `(repository, created_at)`, and `failure_type`

### Analyzer (`analyzer.py`)

#### `CIFailureAnalyzer` class

```python
class CIFailureAnalyzer:
    def analyze(self, raw_log: str) -> AnalysisResult
```

#### `AnalysisResult` dataclass
```python
@dataclass
class AnalysisResult:
    failure_type: str           # One of the failure_type choices
    summary: str                # One-line summary of the failure
    root_cause: str             # Description of the root cause
    error_messages: list[str]   # Extracted error messages
    failed_tests: list[FailedTest]  # List of failed test cases (if test failure)
    stack_traces: list[str]     # Extracted stack traces
    relevant_log_lines: list[LogLine]  # Lines surrounding the failure
    suggestions: list[str]      # Potential fix suggestions
```

#### `FailedTest` dataclass
```python
@dataclass
class FailedTest:
    test_name: str        # Fully qualified test name (e.g., "tests.test_auth.TestLogin.test_invalid_password")
    error_type: str       # Exception class name (e.g., "AssertionError")
    error_message: str    # The assertion or error message
    file_path: str        # Source file path
    line_number: int | None  # Line number if available
```

#### `LogLine` dataclass
```python
@dataclass
class LogLine:
    line_number: int
    content: str
    is_error: bool
```

#### Classification Logic

The analyzer must detect failure types using these patterns:

1. **`test_failure`**: Log contains patterns like `FAILED`, `ERRORS`, `pytest` failure markers (`=== FAILED ===`), `AssertionError`, `unittest` failure patterns, or `jest` test failure patterns (`● Test suite failed`)
2. **`build_error`**: Log contains `error:` from compilers (gcc, rustc, javac), `SyntaxError`, `ModuleNotFoundError`, `Cannot find module`, or build tool errors (`cmake Error`, `make: ***`)
3. **`timeout`**: Log contains `The job running on runner .* has exceeded the maximum time`, `timeout`, or `SIGKILL` after time limit patterns
4. **`infrastructure`**: Log contains `No space left on device`, `unable to access`, `rate limit`, `connection refused`, `ECONNRESET`, or `runner is not available`
5. **`dependency`**: Log contains `Could not resolve dependencies`, `package not found`, `pip install` failures, `npm ERR!`, or `yarn error`
6. **`unknown`**: None of the above patterns match

#### Error Extraction

- Extract Python traceback blocks: from `Traceback (most recent call last):` to the final exception line
- Extract failed pytest test names: parse `FAILED tests/path/test_file.py::TestClass::test_method` patterns
- Extract relevant log lines: 5 lines before and after each error pattern match
- Extract error messages: lines matching `^(Error|ERROR|error):` or `^E\s+` (pytest short format)

### API (`api.py`)

#### `POST /api/0/organizations/{organization_slug}/ci-analysis/`
- Request body: `{"repository": str, "workflow_name": str, "job_name": str, "run_id": int, "job_id": int, "raw_log": str}`
- Creates a `CIBuildFailure` record, runs the analyzer synchronously, stores the result
- Returns `201` with the full analysis result as JSON

#### `GET /api/0/organizations/{organization_slug}/ci-analysis/{id}/`
- Returns the stored analysis result for a given failure record

#### `GET /api/0/organizations/{organization_slug}/ci-analysis/`
- Query parameters: `repository` (optional filter), `failure_type` (optional filter), `limit` (default 20, max 100)
- Returns a paginated list of failure records with analysis results
- Ordered by `created_at` descending

## Expected Functionality

- Submitting a log containing `FAILED tests/test_auth.py::TestLogin::test_invalid_password - AssertionError: 401 != 200` classifies as `test_failure` and extracts the test name, error type, and message
- Submitting a log containing `error: cannot find crate for 'serde'` classifies as `build_error`
- Submitting a log containing `The job running on runner GitHub Actions 4 has exceeded the maximum time limit of 360 minutes` classifies as `timeout`
- The analysis result contains relevant log lines surrounding each error

## Acceptance Criteria

- `CIFailureAnalyzer.analyze` correctly classifies all six failure types based on log content patterns
- Python tracebacks are fully extracted from raw logs
- Failed test names are parsed from pytest output with fully qualified names
- Relevant log context (±5 lines) is included for each error occurrence
- The POST API endpoint creates a record, runs analysis, and returns structured results
- The GET list endpoint supports filtering by repository and failure_type
- All models have proper indexes for query performance
- Edge cases handled: empty logs (classified as `unknown`), logs with multiple failure types (first match wins), very large logs (truncate `relevant_log_lines` to 50 entries)
