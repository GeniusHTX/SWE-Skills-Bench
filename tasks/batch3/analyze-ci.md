# Task: Build a CI Failure Analysis Engine for Sentry's GitHub Actions Workflows

## Background

Sentry (https://github.com/getsentry/sentry) is an application monitoring platform with a complex CI pipeline using GitHub Actions. The project needs a module that can parse GitHub Actions workflow log output, classify failure types, identify root causes, and generate structured failure summaries. This helps developers quickly diagnose CI failures without reading through thousands of log lines.

## Files to Create/Modify

- `src/sentry/utils/ci_analyzer.py` (create) — CI log parser and failure classifier
- `src/sentry/utils/ci_models.py` (create) — Data models for workflow runs, job results, and failure reports
- `tests/sentry/utils/test_ci_analyzer.py` (create) — Tests for CI analysis functionality

## Requirements

### Workflow Log Parsing

- Implement a `CILogParser` class that parses GitHub Actions log output (plain text format with timestamps and group markers)
- Extract structure: workflow name, job names, step names, step durations, step outcomes (success/failure/skipped)
- Recognize GitHub Actions group markers: `::group::Step Name` and `::endgroup::` to associate log lines with steps
- Recognize error annotations: `::error::message` and `::warning::message`, extracting the message and associating it with the current step
- Handle multiline log content: lines between `::group::` and `::endgroup::` belong to that step

### Failure Classification

- Classify each failed step into one of the following categories:
  - `test_failure` — step name contains "test" or "pytest" or "jest" or "check", or log contains assertion error patterns
  - `build_failure` — step name contains "build" or "compile", or log contains compilation error patterns (`error:`, `Error:`, `FAILED`, `BUILD FAILURE`)
  - `dependency_failure` — log contains patterns like `ModuleNotFoundError`, `ImportError`, `npm ERR!`, `Could not resolve dependencies`, `pip install.*failed`
  - `timeout` — log contains `exceeded the maximum execution time`, `timed out`, or `Cancelling since.*passed`
  - `infrastructure` — log contains `Resource not accessible`, `Service Unavailable`, `rate limit`, `ECONNREFUSED`, `no space left on device`
  - `flaky` — same test previously passed in the same workflow (requires cross-referencing with a `previous_results` parameter)
  - `unknown` — does not match any pattern above
- Each classification includes a `confidence` score (0.0–1.0) based on how many patterns matched

### Root Cause Identification

- For `test_failure`: extract the failing test name, assertion message, and file:line reference from the log
- For `build_failure`: extract the first compilation error message and the file path
- For `dependency_failure`: extract the package name and version constraint that failed
- Return a `RootCause` object with: `category`, `summary` (one-line human-readable summary), `details` (extracted specifics), `log_excerpt` (the 10 most relevant log lines around the error)

### Failure Report Generation

- Implement `generate_report(workflow_log: str, previous_results: dict = None) -> FailureReport`
- `FailureReport` contains: `workflow_name`, `total_jobs`, `failed_jobs`, `failures` (list of classified failures with root causes), `summary` (human-readable paragraph summarizing all failures), `suggested_actions` (list of recommended next steps per failure type)
- Suggested actions mapping:
  - `test_failure` → `"Review the failing assertion and check for recent changes to the tested code"`
  - `build_failure` → `"Check for syntax errors or missing imports in the listed file"`
  - `dependency_failure` → `"Verify package versions in requirements/package.json and check for yanked versions"`
  - `timeout` → `"Check for performance regressions or infinite loops in recent changes"`
  - `infrastructure` → `"Retry the workflow; if persistent, check GitHub Status page"`
  - `flaky` → `"Mark the test as flaky and investigate intermittent failures"`

### Expected Functionality

- A log with `::error::FAILED tests/test_auth.py::test_login - AssertionError: 403 != 200` is classified as `test_failure` with the test name `test_auth.py::test_login` extracted
- A log with `npm ERR! Could not resolve dependency: peer react@"^17.0.0"` is classified as `dependency_failure` with package `react` extracted
- A log with `Error: Process completed with exit code 137` and `Cancelling since 360 minutes passed` is classified as `timeout`
- A report for a workflow with 3 failures produces a summary paragraph mentioning all 3 and lists appropriate suggested actions
- If `previous_results` shows `test_login` passed in a prior run, the current failure is classified as `flaky`

## Acceptance Criteria

- `CILogParser` correctly parses GitHub Actions log format, associating lines with steps via group markers
- Error and warning annotations are extracted and linked to their containing steps
- Failure classification assigns correct categories with confidence scores for all defined patterns
- Root cause extraction identifies test names, compilation errors, and package names from log content
- The `log_excerpt` contains the 10 most relevant lines centered around the detected error
- `FailureReport` includes correct failure counts, classified failures, human-readable summary, and appropriate suggested actions
- Flaky test detection works when `previous_results` is provided
- Tests cover all 7 failure categories with representative log samples, multi-failure workflows, and edge cases
