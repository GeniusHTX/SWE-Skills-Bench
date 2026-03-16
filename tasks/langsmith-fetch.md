# Task: Create LangSmith Data Fetch Utility for LangChain

## Background

Create a utility script within the LangChain repository that demonstrates how to fetch run data from LangSmith API and export results to JSON/CSV format.

## Files to Create/Modify

- `examples/langsmith_fetch.py` - Main fetch utility script

## Requirements

### Fetch Utility (langsmith_fetch.py)
- LangSmith client initialization with API key
- Query runs by project name
- Filter by date range (start_date, end_date)
- Pagination handling for large result sets

### Export Features
- JSON export with full run data
- CSV export with selected fields
- Configurable output path via CLI argument

### Fields to Export
- `run_id`
- `inputs`
- `outputs`
- `feedback_scores`
- `start_time`, `end_time`

### CLI Interface
- `--project`: LangSmith project name
- `--output`: Output file path
- `--format`: `json` or `csv`
- `--help`: Show usage information

## Acceptance Criteria

- `python examples/langsmith_fetch.py --help` shows usage
- Script handles API authentication via environment variable
- Output format matches specification (JSON or CSV with correct fields)
