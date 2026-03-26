# Task: Add Profiling-Based Optimization to py-spy's Flamegraph Aggregation Pipeline

## Background

py-spy (https://github.com/benfred/py-spy) is a sampling profiler for Python programs written in Rust. The flamegraph generation pipeline aggregates stack samples into a collapsed format and then renders SVG flamegraphs. As profiling sessions grow large (millions of samples), the aggregation step becomes a bottleneck. This task optimizes the stack frame aggregation and flamegraph data preparation code paths for both CPU time and memory usage.

## Files to Create/Modify

- `src/flamegraph.rs` (modify) — Optimize stack frame aggregation: reduce allocations, use more efficient data structures for frame deduplication
- `src/stack_trace.rs` (modify) — Optimize stack frame representation to reduce memory per frame
- `benches/flamegraph_bench.rs` (create) — Criterion benchmarks for aggregation pipeline with varying sample sizes (1K, 100K, 1M samples)
- `tests/test_flamegraph_perf.rs` (create) — Integration tests verifying output correctness after optimization

## Requirements

### Stack Frame Aggregation Optimization

- The current aggregation builds a tree of stack frames from collapsed stack traces; with 1M+ samples many frames are duplicated
- Deduplicate frame strings using an interning mechanism so identical function names, file paths, and line numbers share a single allocation
- Replace the frame tree's children collection with a structure that avoids repeated linear scans when inserting new child frames
- The aggregation of 1M samples must complete within 2 seconds on a 4-core machine (establish baseline with benchmarks first)

### Memory Optimization

- The `StackFrame` struct currently stores `String` fields for `name`, `filename`, and `module`; these should reference interned strings to reduce per-frame memory
- Peak memory during aggregation of 1M samples with 500 unique frames should not exceed 150MB
- The interning pool must be bounded; if it exceeds a configurable limit (default: 100,000 entries), fall back to regular allocation with a logged warning

### Flamegraph Data Preparation

- The collapsed-format writer iterates the frame tree and produces semicolon-separated lines; optimize this to avoid repeated string concatenation
- Use a single pre-allocated buffer that grows as needed, writing frame paths incrementally
- The output format must be byte-identical to the original implementation for the same input data

### Benchmark Suite

- Create Criterion benchmarks in `benches/flamegraph_bench.rs` with three scenarios:
  - `small` — 1,000 samples, 50 unique frames
  - `medium` — 100,000 samples, 200 unique frames
  - `large` — 1,000,000 samples, 500 unique frames
- Each benchmark measures aggregation time and can be run with `cargo bench`
- Include a memory measurement that tracks peak RSS during the large benchmark

### Expected Functionality

- `cargo bench` runs all three scenarios and reports timing results
- The `large` benchmark completes aggregation within 2 seconds
- The collapsed output for a given set of input samples is byte-identical before and after optimization
- When the intern pool exceeds 100,000 entries, a warning is logged and new strings are allocated normally
- All existing tests in the repository continue to pass after the changes

## Acceptance Criteria

- Stack frame strings are interned so duplicate frames share allocations
- The frame tree uses an efficient lookup structure for child insertion (not linear scan)
- Collapsed-format output is byte-identical to the pre-optimization output for the same inputs
- Criterion benchmarks for small/medium/large scenarios are included and runnable via `cargo bench`
- The large benchmark (1M samples, 500 unique frames) aggregates within 2 seconds
- Peak memory during the large benchmark does not exceed 150MB
- The intern pool is bounded at a configurable limit with fallback to regular allocation
- `cargo build --release` succeeds without warnings and all existing tests pass
