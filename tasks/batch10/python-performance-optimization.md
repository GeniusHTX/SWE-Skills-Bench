# Task: Add CPU and Memory Profiling Support to py-spy's Python Output Formatter

## Background

The `benfred/py-spy` repository is a sampling profiler for Python programs written in Rust. The existing `src/flamegraph.rs` and `src/config.rs` handle stack trace collection and output formatting. A new subcommand `profile-summary` is needed that reads a previously recorded `.spy` or raw stack-trace file, computes per-function cumulative time and call-count statistics, and outputs a sorted plaintext table — enabling developers to identify the hottest functions without an external viewer.

## Files to Create/Modify

- `src/summary.rs` (create) — New module implementing the `profile-summary` subcommand: parses stack frames, aggregates cumulative time per function (`file:line:function_name`), and prints a table sorted by descending cumulative time
- `src/main.rs` (modify) — Add the `profile-summary` subcommand to the CLI argument parser using the existing `clap` setup; wire it to `summary::run`
- `src/config.rs` (modify) — Add `SummaryConfig` struct with fields: `filename: PathBuf`, `top_n: usize` (default 20), `min_pct: f64` (default 0.5), `output_format: SummaryFormat` (enum: `Table`, `Json`)
- `tests/test_summary.rs` (create) — Integration tests that feed a synthetic stack-trace fixture file to `summary::run` and assert correct aggregation output, edge cases for empty input and single frame

## Requirements

### SummaryConfig

- `top_n` must be in range `[1, 1000]`; values outside this range must produce a `ConfigError` before any file is read
- `min_pct` must be in range `[0.0, 100.0]`; out-of-range values must produce a `ConfigError`
- `filename` must be an existing readable file; a missing or unreadable file must produce a `ConfigError` with the OS error message included

### Aggregation Logic

- Each stack frame is identified by the triple `(file, line_number, function_name)`; frames with identical triples must be merged
- Cumulative time for a function is the sum of all samples in which the function appears anywhere in the stack (not just at the top)
- Self time for a function is the count of samples in which the function appears at the top of the stack only
- Output table columns: `rank`, `cumulative_pct`, `self_pct`, `cumulative_samples`, `self_samples`, `function` (formatted as `file:line function_name`)
- Only functions with `cumulative_pct >= min_pct` are included; after filtering, only the top `top_n` entries are printed

### JSON Output Format

When `output_format: Json`, output a JSON array of objects with keys `rank`, `cumulative_pct`, `self_pct`, `cumulative_samples`, `self_samples`, `function`; the array must be sorted by `cumulative_samples` descending

### Expected Functionality

- Input with 100 samples all in function `foo` at `bar.py:10` → `foo` has `cumulative_pct = 100.0`, `self_pct = 100.0`
- Input where `foo` calls `bar`: 80 samples with both in stack, 20 samples with only `bar` → `foo` cumulative=80, self=0; `bar` cumulative=100, self=100 (assuming bar always at top)
- Empty input file (0 bytes) → outputs header row only, no data rows, exit code 0
- Input with all functions below `min_pct` threshold → outputs header row only, no data rows
- `top_n=3` with 10 distinct functions in input → outputs exactly 3 data rows (the top 3 by cumulative time)
- Unreadable input file → exits with non-zero code and prints error message to stderr

## Acceptance Criteria

- `cargo build --release` exits with code 0 after all changes
- Running `py-spy profile-summary --help` displays `SummaryConfig` fields including `--top-n`, `--min-pct`, and `--output-format`
- Given a synthetic fixture with known frame counts, the output table's `cumulative_pct` values match expected calculations to within 0.01%
- JSON output is valid JSON with the required keys and correct sort order
- Out-of-range `--top-n` and `--min-pct` values produce error messages before any file I/O
- Integration tests in `tests/test_summary.rs` all pass via `cargo test`
