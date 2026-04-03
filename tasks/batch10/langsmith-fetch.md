# Task: Build a LangSmith Trace Fetcher CLI for LangChain Agent Debugging

## Background

The `langchain-ai/langchain` repository is the main LangChain Python framework. A new CLI tool `langsmith-fetch` is needed in `libs/langchain/langchain/tools/` that developers can invoke from the terminal to retrieve recent execution traces from LangSmith, format them as a human-readable summary or JSON, and help identify failing tool calls and performance outliers without leaving the terminal.

## Files to Create/Modify

- `libs/langchain/langchain/tools/langsmith_fetch.py` (create) — Core module implementing `LangSmithClient`, `TraceRecord`, and `fetch_traces(project: str, last_n_minutes: int, limit: int) -> list[TraceRecord]`
- `libs/langchain/langchain/tools/langsmith_fetch_cli.py` (create) — CLI entry point using `argparse` with subcommands `traces` and `trace <id>`; reads `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT` from environment
- `libs/langchain/pyproject.toml` (modify) — Register the CLI entry point `langsmith-fetch = langchain.tools.langsmith_fetch_cli:main` under `[project.scripts]`
- `libs/langchain/tests/unit_tests/tools/test_langsmith_fetch.py` (create) — Unit tests using `unittest.mock.patch` to mock HTTP calls; tests cover normal response parsing, empty trace list, malformed API response, and missing environment variables

## Requirements

### TraceRecord Data Class

- `TraceRecord` must be a Python dataclass with fields: `trace_id: str`, `agent_name: str`, `status: str` (one of `"success"`, `"error"`, `"timeout"`), `tools_called: list[str]`, `duration_ms: float`, `token_count: int | None`, `error_message: str | None`
- `status` must be derived from the LangSmith run `status` field: `"success"` when `error` is null and `status == "success"`; `"error"` when `error` is not null; `"timeout"` when `status == "timeout"`

### LangSmithClient

- `LangSmithClient(api_key: str, base_url: str = "https://api.smith.langchain.com")` — constructor stores credentials; `base_url` must not end with `/`
- `fetch_traces(project: str, last_n_minutes: int, limit: int) -> list[TraceRecord]` — calls `GET /api/v1/runs?project_name={project}&start_time={iso_timestamp}&limit={limit}` using `requests`; converts each run to `TraceRecord`
- `fetch_trace(trace_id: str) -> TraceRecord` — calls `GET /api/v1/runs/{trace_id}` and returns a single `TraceRecord`
- HTTP errors (4xx, 5xx) must raise `LangSmithFetchError(status_code, message)` — a custom exception defined in the same module
- When `limit` exceeds 100, it must be clamped to 100 before the API call; no `ValueError` is raised

### CLI Subcommands

- `langsmith-fetch traces [--last-n-minutes N] [--limit N] [--format pretty|json] [--project PROJECT]`
  - Default: `--last-n-minutes 10`, `--limit 10`, `--format pretty`
  - `--project` overrides the `LANGSMITH_PROJECT` env var; if neither is set, exit with code 1 and message `"LANGSMITH_PROJECT not set"`
- `langsmith-fetch trace <trace_id> [--format pretty|json]`
  - Fetches a single trace by ID and prints it

- `pretty` format output must include: trace ID (truncated to 8 chars), status with a symbol (`✅` success, `❌` error, `⏱` timeout), agent name, tools called (comma-separated), duration in ms, and token count if available
- `json` format output must be valid JSON matching the `TraceRecord` field names

### Expected Functionality

- `LANGSMITH_API_KEY` not set in environment → CLI exits with code 1 and prints `"LANGSMITH_API_KEY not set"` to stderr
- API returns 401 → `LangSmithFetchError` raised with `status_code=401`; CLI prints error to stderr and exits code 1
- API returns empty `runs` array → CLI prints `"No traces found"` and exits code 0
- Run with `error` field populated → `TraceRecord.status = "error"` and `error_message` contains the error text
- `limit=150` → actual API call uses `limit=100`

## Acceptance Criteria

- `langsmith-fetch traces --help` displays all flags including `--last-n-minutes`, `--limit`, `--format`, and `--project`
- `langsmith-fetch trace --help` displays `trace_id` as a required positional argument and `--format`
- `fetch_traces` with mocked HTTP returns a list of `TraceRecord` objects with correct field mapping
- Missing `LANGSMITH_API_KEY` causes CLI to exit with code 1 and a descriptive stderr message
- `limit` values above 100 are silently clamped to 100 in the API call, verified by mock assertion
- Unit tests in `test_langsmith_fetch.py` pass via `python -m pytest libs/langchain/tests/unit_tests/tools/test_langsmith_fetch.py -v`
