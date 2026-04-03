# Task: Implement a LangSmith Trace Analyzer for LangChain Agent Debugging

## Background

LangChain (https://github.com/langchain-ai/langchain) is a framework for building LLM applications. When debugging LangChain agents and chains in production, developers need tooling to fetch, parse, and analyze execution traces from LangSmith. The project needs a trace analysis module that can load trace data (from JSON files or API responses), parse the nested run tree structure, detect common failure patterns, and generate diagnostic reports.

## Files to Create/Modify

- `libs/langchain/langchain/smith/trace_analyzer.py` (create) — `TraceAnalyzer` class that loads trace JSON data, parses the run tree into a flat list of spans, detects error patterns, and computes execution statistics
- `libs/langchain/langchain/smith/trace_loader.py` (create) — `TraceLoader` class that reads trace data from JSON files and validates the expected schema (run_id, name, run_type, start_time, end_time, status, child_runs, inputs, outputs, error)
- `libs/langchain/langchain/smith/report_generator.py` (create) — `DiagnosticReport` class that produces a structured summary of trace analysis: execution timeline, error root causes, performance bottlenecks, and tool call sequences
- `tests/test_langsmith_fetch.py` (create) — Tests covering trace loading, parsing, error detection, statistics computation, and report generation

## Requirements

### TraceLoader

- `load_from_file(path: str) -> dict` — Read a JSON file and validate it has required keys: `run_id` (str), `name` (str), `run_type` (str, one of `"chain"`, `"llm"`, `"tool"`, `"retriever"`), `start_time` (ISO 8601 str), `end_time` (ISO 8601 str or null), `status` (str, one of `"success"`, `"error"`, `"pending"`), `child_runs` (list of nested run dicts), `inputs` (dict), `outputs` (dict or null), `error` (str or null)
- `load_from_dict(data: dict) -> dict` — Same validation as above, accepts a raw dict (like from an API response)
- Validation errors raise `ValueError` with the field name and issue (e.g., `"Missing required field: run_id"`)
- If `end_time` is null and `status` is `"success"`, raise `ValueError("Successful run must have end_time")`

### TraceAnalyzer

- Constructor: `TraceAnalyzer(trace: dict)` — Takes a validated trace dict from `TraceLoader`
- `flatten_runs() -> list[dict]` — Recursively flatten the nested `child_runs` tree into a flat list, each run augmented with `depth` (int, root = 0) and `parent_run_id` (str or None)
- `get_timeline() -> list[dict]` — Return all runs sorted by `start_time`, each with `{"run_id": str, "name": str, "run_type": str, "start_time": str, "duration_ms": float, "status": str}`; if `end_time` is null, `duration_ms` is null
- `get_errors() -> list[dict]` — Return all runs with `status == "error"`, each with `{"run_id": str, "name": str, "run_type": str, "error": str, "depth": int, "parent_run_id": str}`
- `get_tool_calls() -> list[dict]` — Return all runs with `run_type == "tool"`, each with `{"run_id": str, "name": str, "inputs": dict, "outputs": dict, "status": str, "duration_ms": float}`
- `get_llm_calls() -> list[dict]` — Return all runs with `run_type == "llm"`, each with `{"run_id": str, "name": str, "duration_ms": float, "status": str, "token_count": int}` where `token_count` is extracted from `outputs.get("llm_output", {}).get("token_usage", {}).get("total_tokens", 0)`
- `compute_statistics() -> dict` — Return:
  - `total_runs`: int
  - `total_duration_ms`: float (root run duration)
  - `error_count`: int
  - `tool_call_count`: int
  - `llm_call_count`: int
  - `total_tokens`: int (sum of all LLM call tokens)
  - `avg_llm_duration_ms`: float (mean of LLM call durations, 0.0 if no LLM calls)
  - `slowest_run`: dict with `run_id`, `name`, `duration_ms`
  - `error_rate`: float (error_count / total_runs)

### Error Pattern Detection

- `detect_patterns() -> list[dict]` — Scan the trace and identify:
  - `"timeout"`: Any run with duration > 30,000ms and status `"error"`
  - `"retry_storm"`: Three or more consecutive tool calls with the same `name` and status `"error"`
  - `"cascading_failure"`: An error run whose parent also has status `"error"`
  - `"empty_retrieval"`: A retriever run where `outputs` is null or `outputs.get("documents", [])` is empty
- Each detected pattern: `{"pattern": str, "run_ids": list[str], "description": str, "severity": str}` where severity is `"critical"` for timeout and retry_storm, `"warning"` for cascading_failure and empty_retrieval

### DiagnosticReport

- Constructor: `DiagnosticReport(analyzer: TraceAnalyzer)`
- `generate() -> dict` with sections:
  - `summary`: Statistics from `compute_statistics()`
  - `timeline`: Ordered execution events from `get_timeline()`
  - `errors`: List from `get_errors()` with root cause annotation (the deepest error in each error chain)
  - `patterns`: Detected patterns from `detect_patterns()`
  - `tool_analysis`: Tool calls with success/failure counts per tool name
  - `performance`: Top 5 slowest runs by duration
- `to_text() -> str` — Human-readable text format of the report, with sections separated by headers and bullet points

### Edge Cases

- Trace with no child runs (single root run): all methods work correctly, returning single-element or empty lists as appropriate
- Trace with deeply nested runs (depth > 10): `flatten_runs()` handles recursion without stack overflow
- Run with `start_time` after `end_time`: raise `ValueError("end_time cannot be before start_time")`
- Multiple root-level errors: all are reported, not just the first one

## Expected Functionality

- Loading a trace JSON file with 3 LLM calls, 2 tool calls, and 1 error produces correct statistics: `total_runs=6`, `error_count=1`, `error_rate≈0.167`
- A trace with a tool called "search_db" failing 3 times in a row triggers the `"retry_storm"` pattern detection
- `DiagnosticReport.to_text()` produces a readable summary like: `"Trace abc-123: 6 runs, 1 error (16.7% error rate), total duration 5230ms"`
- `get_timeline()` returns runs in chronological order regardless of their nesting depth

## Acceptance Criteria

- `TraceLoader` validates required fields and rejects malformed trace data with descriptive error messages
- `TraceAnalyzer.flatten_runs()` correctly converts nested run trees to flat lists with depth and parent references
- Timeline, error, tool, and LLM call extraction methods return correctly filtered and formatted results
- `compute_statistics()` accurately aggregates run counts, durations, tokens, and error rates
- `detect_patterns()` identifies timeout, retry storm, cascading failure, and empty retrieval patterns
- `DiagnosticReport.generate()` produces a structured report and `to_text()` formats it as human-readable text
- All tests pass with `pytest`
