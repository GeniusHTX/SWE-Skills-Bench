# Task: Build a LangSmith Trace Analysis and Export Module for LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) is a framework for building LLM-powered applications. To support debugging and performance analysis of LangChain agent traces, a module is needed that can parse, analyze, and export trace data from LangSmith-compatible trace formats. This module should integrate with the existing `libs/core` package and work with the structured run/trace data format produced by LangChain's callback system.

## Files to Create/Modify

- `libs/core/langchain_core/tracers/trace_analyzer.py` (create) — Trace analysis module: parse run trees, compute latency breakdowns, detect bottlenecks, and export sessions
- `libs/core/langchain_core/tracers/trace_models.py` (create) — Data models for traces, runs, and analysis results
- `libs/core/tests/unit_tests/tracers/test_trace_analyzer.py` (create) — Tests for trace analysis functionality

## Requirements

### Trace Data Models

- Define a `Run` dataclass with fields: `id` (str), `name` (str), `run_type` (one of `"chain"`, `"llm"`, `"tool"`, `"retriever"`), `start_time` (datetime), `end_time` (datetime or None), `status` (one of `"success"`, `"error"`, `"pending"`), `inputs` (dict), `outputs` (dict or None), `error` (str or None), `child_runs` (list of `Run`), `metadata` (dict)
- Define a `TraceSession` dataclass containing: `session_id` (str), `name` (str), `runs` (list of top-level `Run` objects), `created_at` (datetime)
- Validate that `end_time >= start_time` when both are present; raise `ValueError` otherwise
- Validate that `run_type` is one of the allowed values; raise `ValueError` otherwise

### Latency Analysis

- Implement `analyze_latency(run: Run) -> LatencyBreakdown` that computes:
  - `total_duration`: end_time − start_time in milliseconds
  - `self_time`: total_duration minus the sum of child run durations (time spent in this run excluding children)
  - `child_breakdown`: dict mapping child run names to their durations
  - `critical_path`: the ordered list of runs forming the longest sequential execution path (the path that determines overall latency)
- For nested runs (e.g., chain → LLM → tool → LLM), compute the full tree latency breakdown recursively
- If `end_time` is `None` (pending run), use the current time for duration calculation

### Bottleneck Detection

- Implement `detect_bottlenecks(session: TraceSession, threshold_ms: float = 1000) -> list[Bottleneck]`
- A `Bottleneck` is any run where `self_time > threshold_ms`
- Return bottlenecks sorted by self_time descending
- Each `Bottleneck` contains: `run_id`, `run_name`, `run_type`, `self_time_ms`, `percentage_of_total` (self_time / session total duration × 100)

### Error Analysis

- Implement `analyze_errors(session: TraceSession) -> ErrorSummary`
- `ErrorSummary` contains: `total_runs` (int), `failed_runs` (int), `error_rate` (float, 0.0–1.0), `errors_by_type` (dict mapping `run_type` to count of errors), `error_details` (list of `{"run_id", "run_name", "run_type", "error_message"}`)
- Collect errors from all runs in the tree, including deeply nested child runs

### Session Export

- Implement `export_session(session: TraceSession, format: str) -> str`
- Supported formats: `"json"` (pretty-printed, deterministic key order), `"csv"` (flattened: one row per run with columns: id, name, run_type, start_time, end_time, duration_ms, status, error, parent_id)
- JSON export includes the full nested run tree structure
- CSV export flattens the tree; `parent_id` is the id of the parent run (or empty for top-level runs)
- Raise `ValueError` for unsupported formats

### Expected Functionality

- A chain run (2000ms) containing an LLM run (1500ms) and a tool run (300ms) has self_time = 200ms
- The critical path through chain→LLM is [chain, LLM] with total 2000ms
- A session with 50 runs where 3 have errors reports error_rate = 0.06
- `detect_bottlenecks` with threshold 500ms on a session with runs of self_time [100, 200, 600, 1200] returns 2 bottlenecks (600ms and 1200ms runs)
- `export_session(session, "json")` produces valid JSON with sorted keys
- `export_session(session, "xml")` raises `ValueError`
- A run with end_time < start_time raises `ValueError` at construction time

## Acceptance Criteria

- `Run` and `TraceSession` data models validate constraints at construction time
- Latency analysis correctly computes total_duration, self_time, child_breakdown, and critical_path for nested run trees
- Bottleneck detection identifies runs exceeding the threshold and reports correct percentage of total
- Error analysis traverses the full run tree and produces accurate counts, rates, and details by run type
- JSON export is deterministic and valid; CSV export correctly flattens the run tree with parent_id references
- Unsupported export formats raise `ValueError`
- Tests cover single-level and deeply nested runs, pending runs, error scenarios, and export format validation
