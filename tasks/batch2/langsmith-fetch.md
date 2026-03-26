# Task: Create a LangSmith Trace Fetching Example for LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) integrates with LangSmith for tracing and debugging LLM applications. A new example script is needed that demonstrates how to fetch, filter, and display execution traces from LangSmith, enabling developers to debug their agent workflows.

## Files to Create

- `examples/langsmith_fetch.py` — A script that fetches and displays LangSmith execution traces

## Requirements

### Trace Fetching

- Connect to the LangSmith API using environment-based configuration (`LANGSMITH_API_KEY`, `LANGSMITH_ENDPOINT`)
- Fetch recent execution traces for a configurable project name
- Support filtering traces by time range, run type (chain, llm, tool), and status (success, error)

### Trace Display

- Format and print a summary of each trace: run ID, name, run type, status, latency, token usage
- For error traces, display the error message
- Support a verbose mode that shows the full input/output for each run

### Pagination

- Handle paginated API responses when the number of traces exceeds a single page
- Support a configurable limit on the total number of traces to fetch

### Output

- The script must have a `__main__` entry point
- Default output is a formatted table of trace summaries
- Support JSON output mode for programmatic consumption

## Expected Functionality

- Running the script fetches and displays recent LangSmith traces
- Filters narrow the results to relevant traces
- Error traces show diagnostic information

## Acceptance Criteria

- The script can authenticate to LangSmith using environment-based configuration and fetch recent traces for a chosen project.
- Filtering by time range, run type, and status meaningfully narrows the returned trace set.
- Default output shows a readable summary including run identity, status, latency, and token usage when available.
- Error traces include enough diagnostic information to support debugging.
- Pagination and result limits are handled correctly so large trace sets can still be inspected predictably.
