# Task: Optimize Hot Paths in py-spy's Python Stack Sampling Module

## Background

py-spy (https://github.com/benfred/py-spy) is a sampling profiler for Python programs, written in Rust. Its Python-side `py_spy` package includes helper scripts for profile data processing, flame graph generation, and benchmarking. The profile data processing pipeline in `scripts/` currently has performance bottlenecks when handling large profile dumps (> 100K samples): redundant list allocations, inefficient string operations in stack frame deduplication, and unoptimized I/O patterns. This task focuses on profiling these Python scripts and applying targeted optimizations.

## Files to Create/Modify

- `scripts/benchmark_processing.py` (create) — Benchmark script that generates a synthetic profile dump with 100K+ samples and times the processing pipeline end-to-end.
- `scripts/process_profile.py` (modify) — Optimize the stack frame parsing, deduplication, and aggregation logic to reduce memory allocations and CPU time.
- `scripts/flamegraph.py` (modify) — Optimize the flame graph stack folding step: replace string concatenation in the inner loop with a more efficient approach; use streaming I/O.
- `scripts/tests/test_process_profile.py` (create) — Tests verifying correctness of optimized processing against a known reference output, plus regression benchmarks.

## Requirements

### Benchmark Script

- Generate a synthetic profile with configurable sample count (default 100,000), unique stack depths between 5–50 frames, and 500 unique function names.
- Measure and report: total processing time, peak memory usage, and throughput (samples/second).
- Output results as JSON: `{ "samples": N, "time_seconds": X, "peak_memory_mb": Y, "throughput": Z }`.

### Processing Optimizations

- Stack frame deduplication: Replace the current approach (comparing full string representations) with integer-ID-based deduplication using a lookup dictionary.
- Aggregation: Use `collections.Counter` or equivalent O(1) aggregation instead of repeated list scans.
- Stack folding for flame graphs: Build the folded representation using `str.join()` on pre-encoded segments instead of incremental `+=` concatenation.
- File I/O: Read the profile dump in buffered chunks rather than loading the entire file into memory at once.

### Performance Targets

- Processing 100K samples must complete in under 5 seconds on a standard machine (baseline is ~15–20 seconds), representing at least a 3× speedup.
- Peak memory usage for 100K samples must not exceed 200 MB (baseline is ~500 MB).
- Correctness: the optimized output must be byte-identical to the baseline output for the same input.

### Expected Functionality

- `python scripts/benchmark_processing.py --samples 100000` → produces JSON benchmark results showing processing time and memory usage.
- `python scripts/process_profile.py input.prof -o output.txt` → processes the profile dump and outputs folded stacks.
- Running the benchmark before and after optimization demonstrates the speedup.

## Acceptance Criteria

- The benchmark script runs successfully and reports processing time, peak memory, and throughput.
- Processing 100K samples completes at least 3× faster than the unoptimized baseline.
- Peak memory for 100K samples is reduced by at least 50% compared to baseline.
- The optimized output is identical to the reference output for the same input data.
- Tests verify correctness of processing and include a performance regression check.
- `cargo build --release` still succeeds (Rust code is not modified).
