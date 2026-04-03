# Task: Build a LangSmith Trace Analyzer for LangChain Agent Debugging

## Background

LangChain (https://github.com/langchain-ai/langchain) provides agent frameworks and LangSmith is its tracing platform. A new Python tool is needed that fetches LangChain agent execution traces from the LangSmith API, parses the run tree structure (chains, tool calls, LLM invocations, retrieval steps), computes performance metrics (latency, token usage, error rates), detects common failure patterns, and generates structured debugging reports.

## Files to Create/Modify

- `tools/langsmith_analyzer/client.py` (create) — `LangSmithClient` class that wraps the LangSmith REST API to fetch runs, traces, and datasets
- `tools/langsmith_analyzer/parser.py` (create) — `TraceParser` class that traverses the run tree and extracts structured data: LLM calls, tool calls, chain steps, errors, and timing
- `tools/langsmith_analyzer/metrics.py` (create) — `TraceMetrics` class that computes latency breakdown, token usage by step, error rate, tool call success rate, and per-step timing
- `tools/langsmith_analyzer/analyzer.py` (create) — `TraceAnalyzer` class that detects failure patterns (timeout, parsing error, tool failure, context length exceeded, recursive loop)
- `tools/langsmith_analyzer/reporter.py` (create) — `DebugReporter` that formats analysis as terminal-friendly text, Markdown, and JSON
- `tools/langsmith_analyzer/cli.py` (create) — CLI entry point: `langsmith-analyze traces --last-n-minutes N` and `langsmith-analyze trace <trace-id>`
- `tests/test_langsmith_analyzer.py` (create) — Tests using fixture trace data that mirrors the LangSmith API response format

## Requirements

### LangSmith Client (`client.py`)

- Class `LangSmithClient` with `__init__(self, api_key: str, project_name: str, base_url: str = "https://api.smith.langchain.com")`
- Method `list_runs(limit: int = 10, last_n_minutes: int = 5, run_type: Optional[str] = None, error_only: bool = False) -> list[dict]`:
  - GET `/api/v1/runs?project_name={project}&limit={limit}&start_time={iso_timestamp}&is_root=true`
  - Filter by `run_type` if provided (`chain`, `llm`, `tool`, `retriever`)
  - Filter by `error` field if `error_only=True`
  - Authentication: `x-api-key: {api_key}` header
- Method `get_trace(run_id: str) -> dict`:
  - GET `/api/v1/runs/{run_id}` for root run
  - GET `/api/v1/runs?trace_id={run_id}&is_root=false` for child runs
  - Returns merged structure: root run + `children` list recursively ordered by `start_time`
- Handle HTTP errors: 401 → `AuthenticationError`, 404 → `TraceNotFoundError`, 429 → `RateLimitError` (with `retry_after` attribute from header)
- All requests use a session with `timeout=30`

### Trace Parser (`parser.py`)

- Struct `RunNode`:
  - `id: str`, `name: str`, `run_type: str`, `status: str`, `start_time: datetime`, `end_time: Optional[datetime]`
  - `latency_ms: Optional[float]`
  - `inputs: dict`, `outputs: dict`, `error: Optional[str]`
  - `token_usage: Optional[TokenUsage]` (only for LLM runs: `prompt_tokens`, `completion_tokens`, `total_tokens`)
  - `tool_name: Optional[str]` (only for tool runs)
  - `children: list[RunNode]`
- Class `TraceParser` with method `parse(trace_dict: dict) -> RunNode`:
  - Recursively build `RunNode` tree from raw API response
  - For LLM runs: extract token usage from `outputs.llm_output.token_usage` or `outputs.usage_metadata`
  - For tool runs: extract `tool_name` from `name` or `inputs.tool`
  - Parse `start_time`/`end_time` as ISO datetime, compute `latency_ms = (end - start).total_seconds() * 1000`
- Method `flatten(root: RunNode) -> list[RunNode]` — Returns all nodes in depth-first order

### Metrics (`metrics.py`)

- Class `TraceMetrics` with `__init__(self, root: RunNode)`
- Computed properties:
  - `total_latency_ms: float` — root node's latency
  - `llm_calls: list[RunNode]` — all nodes with `run_type == "llm"`
  - `tool_calls: list[RunNode]` — all nodes with `run_type == "tool"`
  - `total_tokens: int` — sum of `total_tokens` across all LLM runs
  - `prompt_tokens: int` — sum of `prompt_tokens` across all LLM runs
  - `completion_tokens: int` — sum of `completion_tokens` across all LLM runs
  - `llm_latency_ms: float` — sum of LLM run latencies (time spent waiting for model)
  - `tool_latency_ms: float` — sum of tool run latencies
  - `overhead_ms: float` — `total_latency_ms - llm_latency_ms - tool_latency_ms`
  - `error_nodes: list[RunNode]` — nodes where `status == "error"` or `error is not None`
  - `tool_success_rate: float` — fraction of tool calls that succeeded
- Method `latency_breakdown() -> dict[str, float]` — Returns `{"llm": ..., "tools": ..., "overhead": ...}` as percentages

### Failure Analyzer (`analyzer.py`)

- Class `TraceAnalyzer` with `detect_failures(root: RunNode) -> list[FailurePattern]`
- `FailurePattern` dataclass: `pattern_type: str`, `description: str`, `affected_nodes: list[str]`, `severity: str` (error/warning), `recommendation: str`
- Patterns to detect:
  - `TIMEOUT`: any node with latency > 30000ms
  - `TOOL_FAILURE`: tool run with `status == "error"`
  - `CONTEXT_LENGTH_EXCEEDED`: error message contains "context" and "length" or "token limit"
  - `PARSING_ERROR`: error message contains "output_parser" or "parse" or chain name contains "Parser"
  - `RECURSIVE_LOOP`: more than 5 nodes with identical `name` in the flattened tree
  - `EMPTY_OUTPUT`: a non-error node where `outputs` is empty dict or `{"output": ""}`
- Each pattern includes a `recommendation` string (e.g., CONTEXT_LENGTH_EXCEEDED → "Reduce input size, use chunking, or switch to a model with larger context window")

### Reporter (`reporter.py`)

- Method `to_text(root: RunNode, metrics: TraceMetrics, failures: list[FailurePattern]) -> str`:
  - Header: trace ID, status, duration, total tokens
  - Latency breakdown table
  - Tool calls list with status (✅/❌), tool name, latency
  - Failure patterns with severity and recommendations
  - Token usage summary (prompt/completion/total)
- Method `to_markdown(root, metrics, failures) -> str`:
  - Same structure with Markdown formatting, tables, and code blocks for errors
- Method `to_json(root, metrics, failures) -> str` — Full JSON with nested structures

### CLI (`cli.py`)

- `langsmith-analyze traces --last-n-minutes 5 [--limit 10] [--error-only] [--format text|json|markdown]`
- `langsmith-analyze trace <trace-id> [--format text|json|markdown]`
- Reads `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT` from environment variables
- Exits with code 1 if auth fails, code 2 if trace not found

### Expected Functionality

- Parsing a trace with 3 LLM calls and 2 tool calls returns a RunNode tree of depth 3 with correct token totals
- `metrics.llm_latency_ms` equals the sum of all LLM node latencies, not the root latency
- `detect_failures` on a trace where a tool failed returns `TOOL_FAILURE` pattern with the failed tool's node ID
- Text report for a successful trace shows green status, token breakdown, and "No issues detected"

## Acceptance Criteria

- Client correctly constructs LangSmith API URLs with project, limit, and timestamp filters
- Authentication header format matches LangSmith's `x-api-key` requirement
- Parser correctly extracts token usage from `outputs.llm_output.token_usage` and `outputs.usage_metadata`
- Latency breakdown sums correctly to total latency with non-negative overhead
- All 6 failure patterns are detectable from error messages and node structure
- CLI exits with correct codes for authentication errors (1) and missing traces (2)
- Reporter text output contains status emoji (✅/❌) for tool calls
- `python -m pytest /workspace/tests/test_langsmith_fetch.py -v --tb=short` passes
