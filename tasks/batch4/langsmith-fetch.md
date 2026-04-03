# Task: Build a LangSmith Trace Fetcher and Analyzer Library for LangChain

## Background

The LangChain repository (https://github.com/langchain-ai/langchain) provides building blocks for LLM applications. A new debugging module is needed that fetches execution traces from the LangSmith API, parses trace data to extract tool calls, token usage, latency, and errors, classifies run outcomes, and generates structured debug reports — enabling developers to programmatically diagnose agent issues without using the web UI.

## Files to Create/Modify

- `libs/langchain/langchain/debug/trace_fetcher.py` (create) — Client for fetching traces and runs from the LangSmith REST API
- `libs/langchain/langchain/debug/trace_parser.py` (create) — Parses raw trace data into structured objects with tool calls, token counts, and error extraction
- `libs/langchain/langchain/debug/analyzer.py` (create) — Analyzes parsed traces to identify patterns: slow tools, error-prone chains, token budget issues
- `libs/langchain/langchain/debug/reporter.py` (create) — Generates formatted debug reports (text, JSON, markdown)
- `libs/langchain/tests/unit_tests/debug/test_langsmith_fetch.py` (create) — Tests for fetching, parsing, analysis, and reporting

## Requirements

### Trace Fetcher (trace_fetcher.py)

- `TraceFetcher` class accepting: `api_key` (str), `project_name` (str), `base_url` (str, default `"https://api.smith.langchain.com"`)
- `fetch_recent(last_n_minutes: int = 5, limit: int = 10) -> list[dict]` — fetches recent traces from the LangSmith API, returns raw trace dicts
- `fetch_trace(trace_id: str) -> dict` — fetches a single trace by ID with full run tree
- `fetch_runs(trace_id: str) -> list[dict]` — fetches all runs (spans) within a trace
- API calls must include `X-API-Key` header and use a 30-second timeout
- Must handle HTTP errors: 401 → raise `AuthenticationError`, 404 → raise `TraceNotFoundError`, 429 → raise `RateLimitError`, others → raise `LangSmithAPIError`
- All custom exceptions must inherit from a base `LangSmithError` class

### Trace Parser (trace_parser.py)

- `ParsedTrace` dataclass with fields: `trace_id`, `name`, `status` (success/error), `start_time`, `end_time`, `duration_ms`, `total_tokens`, `prompt_tokens`, `completion_tokens`, `tool_calls` (list), `errors` (list), `runs` (list of `ParsedRun`)
- `ParsedRun` dataclass with fields: `run_id`, `name`, `run_type` (chain/llm/tool/retriever), `status`, `duration_ms`, `input_preview` (first 200 chars), `output_preview` (first 200 chars), `error` (str or None), `tokens` (dict)
- `parse_trace(raw_trace: dict, raw_runs: list[dict]) -> ParsedTrace` — transforms raw API data into structured objects
- Must handle missing fields gracefully (default to None/0/empty list)

### Analyzer (analyzer.py)

- `TraceAnalyzer` class
- `analyze(traces: list[ParsedTrace]) -> AnalysisResult`
- `AnalysisResult` fields:
  - `total_traces`: int
  - `success_count`: int, `error_count`: int
  - `success_rate`: float (0.0–1.0)
  - `avg_duration_ms`: float
  - `p95_duration_ms`: float
  - `total_tokens_used`: int
  - `avg_tokens_per_trace`: float
  - `slowest_tools`: list of `(tool_name, avg_duration_ms)` sorted descending, top 5
  - `error_patterns`: list of `(error_message, count)` sorted by count descending
  - `recommendations`: list of str — generated based on analysis (e.g., "Tool 'search' averages 5s — consider caching" if avg > 3s; "Error rate 15% — investigate 'timeout' errors" if rate > 10%)
- Recommendations must be generated from concrete thresholds, not arbitrary text

### Reporter (reporter.py)

- `DebugReporter` class
- `report_text(analysis: AnalysisResult) -> str` — human-readable text report with sections for overview, performance, errors, and recommendations
- `report_json(analysis: AnalysisResult) -> str` — JSON serializable report
- `report_markdown(analysis: AnalysisResult) -> str` — markdown-formatted report with tables for slowest tools and error patterns
- `report_trace_detail(trace: ParsedTrace) -> str` — detailed single-trace report showing the full run tree with indentation for nested runs

### Expected Functionality

- `TraceFetcher` with a valid API key fetches recent traces from LangSmith
- `parse_trace` on a raw trace with 3 tool calls and 1 error produces a `ParsedTrace` with correct `tool_calls`, `errors`, and `total_tokens`
- Analyzing 10 traces (8 success, 2 errors) produces `success_rate=0.8` and lists the error patterns
- The analyzer recommends caching for tools averaging > 3 seconds
- A markdown report for 10 analyzed traces includes a table of slowest tools and a recommendations section
- Fetching a non-existent trace raises `TraceNotFoundError`

## Acceptance Criteria

- TraceFetcher correctly constructs API requests with authentication and handles all HTTP error codes
- Custom exception hierarchy allows catching all LangSmith errors via the base class
- Trace parser transforms raw API responses into structured `ParsedTrace` objects with correct token counts and durations
- Analyzer computes accurate statistics including success rate, P95 latency, and token usage
- Recommendations are generated from measurable thresholds (tool latency > 3s, error rate > 10%)
- Reporter produces valid text, JSON, and markdown output formats
- Tests verify API error handling, parsing of various trace structures, analysis statistics, and report formatting
