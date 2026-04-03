# Task: Build a CPU Profiling Aggregation and Flame Graph Filter Tool for py-spy

## Background

The py-spy project (https://github.com/benfred/py-spy) is a sampling profiler for Python programs. Currently, py-spy outputs raw profiling data (stack traces with sample counts) but lacks built-in tooling for aggregating profiles across multiple runs, filtering flame graph data by module or function name, and generating summary reports. A post-processing tool is needed that reads py-spy output files, aggregates them, and produces filtered/summarized results.

## Files to Create/Modify

- `scripts/profile_aggregator.py` (create) — CLI tool that reads one or more py-spy speedscope JSON output files, merges sample data, and produces an aggregated profile
- `scripts/flamegraph_filter.py` (create) — CLI tool that filters flame graph data by module name, function name regex, or minimum sample threshold
- `scripts/profile_report.py` (create) — Generates a human-readable summary report from aggregated profile data: top-N hottest functions, per-module breakdown, and call-chain analysis
- `tests/test_profile_aggregator.py` (create) — Tests for merging multiple profile files, handling mismatched schemas, and sample count arithmetic
- `tests/test_flamegraph_filter.py` (create) — Tests for filtering by module, regex, threshold, and combined filters

## Requirements

### Profile Aggregation

- Read py-spy output in speedscope JSON format (the format produced by `py-spy record --format speedscope`).
- Accept one or more input file paths on the command line.
- Merge stack frames across files: identical call stacks must have their sample counts summed.
- The output must be valid speedscope JSON that can be loaded in https://www.speedscope.app/.
- Handle the case where input files have different Python processes or thread names — merge by thread name, keeping separate profiles for distinct threads.
- If input files contain incompatible schemas (missing required fields), emit a clear error and exit with code 1.

### Flame Graph Filtering

- Accept a single speedscope JSON input file and produce a filtered version.
- Support the following filter flags (combinable):
  - `--module <name>` — keep only frames where the module path contains the given string (e.g., `--module myapp` keeps frames from `myapp/views.py`, `myapp/models.py`).
  - `--function <regex>` — keep only frames where the function name matches the Python regex pattern.
  - `--min-samples <N>` — remove all call stacks with fewer than N total samples.
  - `--exclude-module <name>` — remove frames from the specified module (e.g., `--exclude-module importlib` to hide import machinery).
- When a frame is removed by filtering, its children must be re-parented to the filtered frame's parent to maintain a valid flame graph structure.
- Output is valid speedscope JSON.

### Summary Report

- Read a speedscope JSON file and output a text report to stdout.
- The report must include:
  - **Top 20 hottest functions**: function name, module, self-sample count, cumulative sample count, percentage of total.
  - **Per-module breakdown**: module name, total samples, percentage, sorted descending.
  - **Deepest call chain**: the longest call stack observed, printed as `module.function → module.function → ...`.
  - **Total samples** and **total unique functions** seen.
- Support `--top N` flag to change the number of hottest functions shown (default 20).
- Support `--format` flag with values `text` (default) and `json`.

### Error Handling

- Non-existent input files → clear error message naming the missing file, exit code 1.
- Malformed JSON input → error `"Failed to parse {filename}: {reason}"`, exit code 1.
- `--function` with invalid regex → error `"Invalid regex pattern: {pattern}"`, exit code 1.
- `--min-samples` with non-positive value → error `"--min-samples must be a positive integer"`, exit code 1.

### Expected Functionality

- `python scripts/profile_aggregator.py run1.json run2.json -o merged.json` → produces a merged speedscope file where shared call stacks have summed sample counts.
- `python scripts/flamegraph_filter.py profile.json --module myapp --min-samples 5 -o filtered.json` → outputs a filtered profile containing only frames from `myapp` modules with ≥5 samples.
- `python scripts/flamegraph_filter.py profile.json --exclude-module importlib --function "process_.*"` → removes importlib frames and keeps only functions matching `process_.*`.
- `python scripts/profile_report.py profile.json --top 10` → prints a summary with the 10 hottest functions, per-module table, and deepest call chain.
- `python scripts/profile_report.py profile.json --format json` → outputs the same report as structured JSON.

## Acceptance Criteria

- The aggregator correctly merges multiple speedscope JSON files with summed sample counts for identical call stacks.
- The filtered output is valid speedscope JSON loadable in speedscope.app.
- Module and function filters correctly include/exclude frames while maintaining valid flame graph parent-child relationships.
- The summary report correctly ranks functions by self-sample count and aggregates per-module totals.
- All CLI tools handle missing files, malformed input, and invalid arguments with descriptive error messages and non-zero exit codes.
- The project builds with `cargo build --release` without errors (the Rust profiler core) and the Python scripts run independently.
