# Task: Debug and Analyze a Failing LangGraph Agent Using LangSmith Traces

## Background

A LangGraph-based research agent deployed in production is experiencing intermittent failures. Users report that the agent sometimes returns empty responses, other times it loops indefinitely through tool calls, and occasionally it generates answers that ignore the retrieved context. The debugging process requires fetching execution traces from LangSmith, analyzing execution patterns, identifying root causes, and producing a diagnostic report.

## Files to Create/Modify

- `scripts/debug_agent.sh` (create) — Shell script that fetches recent traces, filters failures, and exports diagnostic data
- `scripts/analyze_traces.py` (create) — Python script that parses exported trace JSON and produces a structured diagnostic report
- `reports/agent_diagnostic.md` (create) — Generated Markdown report with findings, root causes, and recommended fixes

## Requirements

### Trace Fetching Script (`scripts/debug_agent.sh`)

The script must execute the following `langsmith-fetch` commands in sequence:

1. **Fetch recent traces** — retrieve the last 60 minutes of traces, limit 50:
   ```
   langsmith-fetch traces traces_raw --last-n-minutes 60 --limit 50 --format json --include-metadata
   ```

2. **Identify failing traces** — from the raw traces, extract trace IDs where `status == "error"` or `execution_time > 30000` (ms) using `jq` or Python one-liner:
   ```
   cat traces_raw/*.json | python3 -c "import json,sys; data=json.load(sys.stdin); [print(t['trace_id']) for t in data if t.get('error') or t.get('execution_time',0)>30000]" > failing_trace_ids.txt
   ```

3. **Deep fetch each failing trace** — for each trace ID in `failing_trace_ids.txt`:
   ```
   langsmith-fetch trace <trace-id> --format json > traces_detailed/<trace-id>.json
   ```

4. **Fetch recent threads** — get conversation threads from the last 60 minutes:
   ```
   langsmith-fetch threads threads_raw --limit 20
   ```

5. **Create session export** — organize all output into a timestamped directory:
   ```
   SESSION_DIR="langsmith-debug/session-$(date +%Y%m%d-%H%M%S)"
   ```

The script must:
- Create all output directories before writing.
- Exit with error code 1 if `LANGSMITH_API_KEY` or `LANGSMITH_PROJECT` environment variables are not set.
- Print a summary line: `"Fetched N total traces, M failures identified"`.

### Trace Analysis Script (`scripts/analyze_traces.py`)

- Parse all JSON files in the `traces_detailed/` directory.
- For each trace, extract:
  - `trace_id` — string
  - `start_time`, `end_time` — ISO timestamps
  - `execution_time_ms` — integer
  - `status` — `"success"` or `"error"`
  - `error_message` — string or None
  - `tool_calls` — list of `{"tool_name": str, "input": dict, "output": str, "duration_ms": int, "status": str}`
  - `llm_calls` — list of `{"model": str, "prompt_tokens": int, "completion_tokens": int, "duration_ms": int}`
  - `total_tokens` — sum of all LLM call tokens

- Detect the following failure patterns:
  1. **Empty Response** — trace completed but final output is empty string or None. Flag: `"empty_response"`.
  2. **Tool Loop** — same tool called more than 3 times consecutively with identical or near-identical inputs. Flag: `"tool_loop"`. Report the tool name and number of repeated calls.
  3. **Context Ignored** — a `retrieve_documents` tool returned non-empty results, but the subsequent LLM call's output does not reference any keywords from the retrieved documents (check for at least 2 keyword overlaps). Flag: `"context_ignored"`.
  4. **Timeout** — execution time exceeds 30 seconds. Flag: `"timeout"`.
  5. **Tool Error** — any tool call returned with `status: "error"`. Flag: `"tool_error"`. Report tool name and error message.

- Aggregate statistics:
  - Total traces analyzed
  - Failure rate (percentage of error traces)
  - Mean and p95 execution time
  - Most common failure pattern (by count)
  - Most failing tool (by error count)
  - Average token usage per trace

- Output a JSON report to `reports/agent_diagnostic.json` with structure:
  ```json
  {
    "summary": { "total_traces": int, "failure_rate": float, "mean_execution_ms": int, "p95_execution_ms": int, "avg_tokens_per_trace": int },
    "failure_patterns": { "empty_response": int, "tool_loop": int, "context_ignored": int, "timeout": int, "tool_error": int },
    "failing_traces": [ { "trace_id": str, "flags": [str], "error_message": str, "execution_time_ms": int, "tool_calls_count": int } ],
    "recommendations": [str]
  }
  ```

- Generate recommendations based on detected patterns:
  - If `tool_loop > 0`: `"Add max-iteration guard to the agent's tool-calling loop (currently no limit). Set max_iterations=10 in the agent config."`
  - If `context_ignored > 0`: `"The generate node is not incorporating retrieved context. Check the RAG prompt template — ensure context is placed before the question in the prompt."`
  - If `empty_response > 0`: `"Add output validation in the final node: if answer is empty, trigger a retry with explicit instruction 'You must provide an answer based on the context.'"`
  - If `timeout > 0`: `"Set a 25-second timeout on individual tool calls. The retrieve_documents tool is the primary bottleneck — consider adding a query cache."`
  - If `tool_error > 0`: `"Add retry logic with exponential backoff to the failing tool(s). Current tool errors are unhandled."`

### Diagnostic Report (`reports/agent_diagnostic.md`)

Generate a Markdown report from the JSON analysis with sections:

1. **Executive Summary** — one paragraph with total traces, failure rate, most common issue.
2. **Failure Pattern Breakdown** — table with pattern name, count, percentage.
3. **Detailed Failing Traces** — for each failing trace: trace ID, timestamp, duration, flags, error message, tool call sequence.
4. **Token Usage** — average, min, max tokens per trace.
5. **Recommendations** — numbered list of actionable fixes from the analysis.
6. **Raw Data Location** — paths to the exported trace files and JSON report.

### Expected Functionality

- Running `bash scripts/debug_agent.sh` with valid LangSmith credentials → creates `langsmith-debug/session-{timestamp}/` with `traces_raw/`, `traces_detailed/`, `threads_raw/`, `failing_trace_ids.txt`.
- Running `python scripts/analyze_traces.py` on the exported traces → produces `reports/agent_diagnostic.json` with correct failure counts and `reports/agent_diagnostic.md` with formatted report.
- A trace where `search_web` is called 5 times with the same query → flagged as `"tool_loop"` with detail `"search_web called 5 times consecutively"`.
- A trace completion with empty final output → flagged as `"empty_response"`.
- The recommendations list has exactly one entry per detected pattern type (no duplicates).

## Acceptance Criteria

- The fetch script validates environment variables and exits with code 1 if missing.
- The fetch script retrieves traces, identifies failures by error status or execution time >30s, and deep-fetches each failing trace.
- The analysis script detects all 5 failure patterns (empty response, tool loop, context ignored, timeout, tool error) from trace JSON.
- Tool loop detection identifies consecutive identical tool calls (3+ repetitions of the same tool with same inputs).
- Context-ignored detection checks keyword overlap between retrieved documents and the LLM's generated answer.
- The JSON report includes summary statistics, per-pattern counts, individual failing trace details, and pattern-specific recommendations.
- The Markdown report contains all 6 sections with formatted tables and actionable recommendation list.
