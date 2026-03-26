# Task: Create a CI Failure Analysis Script for Sentry

## Background

Sentry (https://github.com/getsentry/sentry) is an error tracking platform with extensive CI pipelines. A new script is needed that parses pytest output logs from failed CI runs, categorizes the failures, and produces a structured analysis report to help developers quickly identify root causes.

## Files to Create

- `scripts/analyze_ci_failures.py` — CI failure analysis script

## Requirements

### Log Parsing

- Parse pytest output (stdout/stderr) from a failed CI run provided as a file path or stdin
- Extract individual test failure records including: test name, file path, failure type (assertion error, exception, timeout), and the error message
- Handle multi-line tracebacks and nested exception chains

### Failure Categorization

- Categorize failures into groups: assertion failures, import errors, timeout errors, infrastructure flakes, and uncategorized
- Count occurrences per category and identify the most-affected test files

### Report Generation

- Output a structured summary report containing:
  - Total tests run, passed, failed, and skipped
  - Failure breakdown by category
  - Top N most-failing test files
  - Individual failure details (test name, category, error excerpt)
- Support output as both human-readable text and structured JSON

### CLI Interface

- Accept input file path and output format as command-line arguments
- The script must have a `__main__` entry point for direct execution

## Expected Functionality

- Given a pytest log with various failure types, the script produces an accurate categorized report
- The report correctly counts and categorizes all failures
- Both text and JSON output formats are well-structured

## Acceptance Criteria

- The script can read pytest failure output from either a file path or standard input.
- Individual failures are extracted with test name, file path, failure category, and a useful error excerpt.
- Multi-line tracebacks and chained exceptions are handled without losing the relationship between failures and their details.
- The generated report includes totals, category counts, top failing files, and individual failure summaries.
- Both human-readable output and JSON output are available and contain equivalent information.
