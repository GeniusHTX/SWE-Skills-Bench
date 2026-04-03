# Task: Implement a LangSmith Trace Analyzer for LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) integrates with LangSmith for trace logging. The task is to implement a Python `TraceAnalyzer` class in the LangChain library that fetches recent execution traces from the LangSmith API, extracts per-run statistics (token usage, latency, errors, tool calls), and produces a structured analysis report for debugging agent behavior.

## Files to Create/Modify

- `libs/langchain/langchain/smith/trace_analyzer.py` (create) — `TraceAnalyzer` class that fetches and analyzes LangSmith traces
- `libs/langchain/langchain/smith/trace_report.py` (create) — Data classes for the trace analysis report
- `libs/langchain/tests/unit_tests/smith/test_trace_analyzer.py` (create) — Unit tests for the analyzer with mocked LangSmith client

## Requirements

### Data Classes (`trace_report.py`)

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class RunStats:
    run_id: str
    name: str                       # e.g., "ChatOpenAI", "AgentExecutor"
    run_type: str                   # "llm", "chain", "tool", "retriever"
    status: str                     # "success", "error"
    start_time: datetime
    end_time: Optional[datetime]
    latency_ms: Optional[float]     # (end_time - start_time).total_seconds() * 1000
    prompt_tokens: int              # 0 if not an LLM run
    completion_tokens: int
    total_tokens: int
    error: Optional[str]            # Error message if status == "error"
    tool_name: Optional[str]        # Populated for run_type == "tool"
    
    @property
    def success(self) -> bool:
        return self.status == "success"

@dataclass
class TraceReport:
    project_name: str
    fetched_at: datetime
    total_traces: int
    runs: list[RunStats]
    
    @property
    def error_runs(self) -> list[RunStats]:
        return [r for r in self.runs if r.status == "error"]
    
    @property
    def tool_calls(self) -> list[RunStats]:
        return [r for r in self.runs if r.run_type == "tool"]
    
    @property
    def llm_runs(self) -> list[RunStats]:
        return [r for r in self.runs if r.run_type == "llm"]
    
    @property
    def total_tokens(self) -> int:
        return sum(r.total_tokens for r in self.runs)
    
    @property
    def avg_latency_ms(self) -> Optional[float]:
        latencies = [r.latency_ms for r in self.runs if r.latency_ms is not None]
        return sum(latencies) / len(latencies) if latencies else None
    
    @property
    def p95_latency_ms(self) -> Optional[float]:
        latencies = sorted(r.latency_ms for r in self.runs if r.latency_ms is not None)
        if not latencies:
            return None
        idx = int(len(latencies) * 0.95)
        return latencies[min(idx, len(latencies) - 1)]
    
    def to_summary_text(self) -> str:
        """Human-readable summary for terminal output."""
```

### `TraceAnalyzer` (`trace_analyzer.py`)

```python
from langsmith import Client
from langchain.smith.trace_report import TraceReport, RunStats

class TraceAnalyzer:
    def __init__(
        self,
        client: Optional[Client] = None,
        project_name: Optional[str] = None,
    ):
        """
        If client is None, instantiate langsmith.Client() (uses LANGSMITH_API_KEY env var).
        If project_name is None, uses LANGSMITH_PROJECT env var.
        """
    
    def fetch_recent(
        self,
        last_n_minutes: int = 5,
        limit: int = 10,
        run_types: Optional[list[str]] = None,   # Filter by run type: ["llm", "chain", "tool"]
        error_only: bool = False,                  # If True, only fetch failed runs
    ) -> TraceReport:
        """Fetch recent runs and return a TraceReport."""
    
    def fetch_by_trace_id(self, trace_id: str) -> TraceReport:
        """Fetch all runs belonging to a single trace ID."""
    
    def _run_to_stats(self, run) -> RunStats:
        """Convert a LangSmith Run object to a RunStats dataclass."""
```

#### `fetch_recent` Logic

1. Compute `start_time = datetime.utcnow() - timedelta(minutes=last_n_minutes)`
2. Call `self.client.list_runs(project_name=self.project_name, start_time=start_time, run_type=run_types, error=error_only if error_only else None, limit=limit)`
3. Convert each run to `RunStats` via `_run_to_stats`
4. Return a `TraceReport` with `project_name`, `fetched_at=datetime.utcnow()`, `total_traces=len(runs)`, `runs=runs`

#### `_run_to_stats` Logic

Map LangSmith `Run` object fields:
- `run.id` → `run_id`
- `run.name` → `name`
- `run.run_type` → `run_type`
- `run.status` → `status` (normalize: `"success"` if `run.error is None`, else `"error"`)
- `run.start_time` → `start_time`
- `run.end_time` → `end_time`
- `latency_ms`: `(run.end_time - run.start_time).total_seconds() * 1000` if both are present, else `None`
- Token counts: from `run.outputs.get("llm_output", {}).get("token_usage", {})` if `run_type == "llm"`, else 0
- `error`: `str(run.error)` if error is present, else `None`
- `tool_name`: `run.name` if `run_type == "tool"`, else `None`

#### `to_summary_text()` Output Format

```
=== LangSmith Trace Analysis ===
Project: my-project | Fetched at: 2024-01-15 10:30:00 UTC | Runs: 15

Summary:
  Total tokens:      2,345
  Avg latency:       1,234ms
  P95 latency:       3,456ms
  Errors:            2 / 15 (13.3%)

Tool Calls (3):
  search_web             2 calls
  get_weather            1 call

LLM Runs (8):
  ChatOpenAI             8 calls | 2,345 tokens

Errors:
  [chain] AgentExecutor: ValueError: Tool 'unknown_tool' not found
  [tool]  search_web: ConnectionTimeout after 30s
```

## Expected Functionality

- `fetch_recent(last_n_minutes=5, limit=10)` calls `client.list_runs` with `start_time` set to 5 minutes ago and `limit=10`
- `_run_to_stats` correctly computes `latency_ms` from `start_time` and `end_time`
- `TraceReport.error_runs` returns only runs where `status == "error"`
- `TraceReport.total_tokens` sums all `total_tokens` across all runs
- `to_summary_text()` produces the formatted multi-section summary

## Acceptance Criteria

- `TraceAnalyzer.__init__` instantiates `Client()` when no client is provided
- `fetch_recent` passes the correct `start_time` (utcnow minus last_n_minutes) to `list_runs`
- `_run_to_stats` correctly maps all LangSmith Run fields including token counts and tool names
- `latency_ms` is `None` when either `start_time` or `end_time` is `None`
- Status normalization: `run.error is None` → `"success"`, otherwise `"error"` regardless of `run.status` value
- `p95_latency_ms` correctly returns the 95th percentile value
- `to_summary_text()` includes all five sections with correct counts
- Unit tests mock `Client.list_runs` and verify that `TraceReport` fields are populated correctly for LLM runs, tool runs, and error runs
