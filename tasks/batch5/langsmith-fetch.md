# Task: Build a LangSmith Run Trace Fetcher and Quality Dashboard

## Background

LangChain (https://github.com/langchain-ai/langchain) includes integration with LangSmith for tracing and monitoring LLM applications. This task requires building a Python module that fetches LangSmith run traces (via the LangSmith client SDK), analyzes them for quality metrics (latency, token usage, error rates), and produces a summary report. The module should work within the LangChain ecosystem and be usable as a standalone CLI tool.

## Files to Create/Modify

- `libs/community/langchain_community/callbacks/langsmith_fetcher.py` (create) — `LangSmithFetcher` class: connects to the LangSmith API, fetches runs filtered by project name, date range, and run type. Supports pagination for large result sets.
- `libs/community/langchain_community/callbacks/trace_analyzer.py` (create) — `TraceAnalyzer` class: takes a list of run traces and computes quality metrics: P50/P95/P99 latency, total/average token usage, error rate, most common error types, and per-model token distribution.
- `libs/community/langchain_community/callbacks/quality_report.py` (create) — `QualityReportGenerator`: takes analyzer output and generates a Markdown report with summary statistics, a latency distribution table (bucketed), and a list of top-5 slowest runs with their IDs.
- `libs/community/langchain_community/callbacks/cli.py` (create) — CLI entry point using `argparse`: accepts `--project`, `--start-date`, `--end-date`, `--output` (file path), and `--format` (markdown or json).
- `libs/community/tests/unit_tests/callbacks/test_langsmith_fetcher.py` (create) — Tests with mocked LangSmith API responses validating fetch, analysis, and report generation.

## Requirements

### LangSmithFetcher

- `LangSmithFetcher(api_key, api_url="https://api.smith.langchain.com")` — initialize with API credentials.
- `fetch_runs(project_name, start_date, end_date, run_type="chain", limit=1000)` — fetch runs matching the filters. Handle pagination if results exceed `limit` by following cursor-based pagination.
- Return a list of `RunTrace` dataclass objects with fields: `id`, `name`, `run_type`, `start_time`, `end_time`, `latency_ms`, `total_tokens`, `prompt_tokens`, `completion_tokens`, `status` (success/error), `error_message`, `model_name`.
- If the API returns a 401, raise `AuthenticationError` with a descriptive message.

### TraceAnalyzer

- `TraceAnalyzer(runs: list[RunTrace])`.
- `compute_latency_stats()` → dict with keys `p50`, `p95`, `p99`, `mean`, `min`, `max` (all in milliseconds).
- `compute_token_stats()` → dict with `total_tokens`, `avg_tokens_per_run`, `total_prompt_tokens`, `total_completion_tokens`.
- `compute_error_stats()` → dict with `total_errors`, `error_rate` (0.0–1.0), `error_types` (Counter of error messages).
- `compute_model_distribution()` → dict mapping model names to `{"count": int, "total_tokens": int, "avg_latency_ms": float}`.
- `summary()` → combined dict of all stats above.

### Quality Report Generator

- `generate_markdown(summary, top_n_slowest=5)` → Markdown string with:
  - Header with project name and date range.
  - Summary table: total runs, error rate, P50/P95 latency, total tokens.
  - Latency distribution: bucket runs into `<100ms`, `100-500ms`, `500ms-1s`, `1-5s`, `>5s` and show count per bucket.
  - Top-N slowest runs table with run ID, name, latency, and model.
- `generate_json(summary)` → JSON string of the full summary dict.

### Expected Functionality

- Fetching 500 runs for project "prod-chatbot" over the last 7 days → returns 500 `RunTrace` objects.
- Analyzer on 500 runs with 10 errors → `error_rate = 0.02`, `error_types` shows counts per error message.
- Report shows latency P50=120ms, P95=850ms correctly when computed on the run data.
- CLI `python -m langchain_community.callbacks.cli --project prod-chatbot --start-date 2024-01-01 --end-date 2024-01-07 --output report.md --format markdown` generates the report file.

## Acceptance Criteria

- `LangSmithFetcher` handles pagination and converts API responses to typed `RunTrace` dataclasses.
- `TraceAnalyzer` correctly computes percentile latencies, token stats, error rates, and model distributions.
- Report generator produces well-formatted Markdown with summary table, latency distribution, and slowest runs.
- CLI accepts required arguments and generates output in the specified format.
- Tests mock the LangSmith API and verify all computation logic against known inputs.
