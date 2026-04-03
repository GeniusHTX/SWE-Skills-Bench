# Task: Add Profiling Benchmark Suite to py-spy

## Background

py-spy (https://github.com/benfred/py-spy) is a sampling profiler for Python programs written in Rust. It can profile running Python processes without modifying them. The project needs a comprehensive benchmark suite that exercises py-spy's profiling capabilities against known Python workloads — CPU-bound, memory-bound, I/O-bound, and multi-threaded — with automated performance regression detection. The benchmark suite must produce reproducible results that can be compared across commits.

## Files to Create/Modify

- `benchmarks/workloads/cpu_bound.py` (create) — CPU-intensive workload: matrix multiplication using nested loops, recursive Fibonacci, and prime sieve computation
- `benchmarks/workloads/memory_bound.py` (create) — Memory-intensive workload: large dictionary creation, list comprehension chaining, and repeated string concatenation with controlled allocation patterns
- `benchmarks/workloads/io_bound.py` (create) — I/O-bound workload: file reads/writes with `os.fsync`, simulated network delays with `time.sleep`, and mixed compute-then-write cycles
- `benchmarks/workloads/threaded.py` (create) — Multi-threaded workload: 4 threads performing distinct tasks (compute, sleep, allocate, file I/O) with a shared counter protected by `threading.Lock`
- `benchmarks/runner.py` (create) — Benchmark orchestrator that launches each workload as a subprocess, attaches py-spy, collects profiling output, and measures overhead (wall-clock slowdown, memory delta)
- `benchmarks/analysis.py` (create) — Result analysis module that parses py-spy output (flamegraph SVG and speedscope JSON), computes summary metrics (top functions by sample count, call-stack depth distribution), and compares against a baseline file
- `benchmarks/baseline.json` (create) — Reference baseline of expected timing and sampling results for regression comparison
- `benchmarks/README.md` (create) — Documentation on running benchmarks and interpreting results

## Requirements

### Workload Design

- Each workload must run for a configurable duration (default 10 seconds) controlled by a `--duration` CLI argument
- Each workload must print `READY` to stdout when it enters its main loop, allowing the runner to synchronize py-spy attachment
- The CPU-bound workload must include at least three distinct functions that each consume ≥ 10% of sampling time, verifiable in the profiling output
- The threaded workload must use exactly 4 threads with distinct names (`compute`, `sleep`, `allocate`, `io`) so py-spy can attribute samples per thread
- Workloads must not use any external dependencies — standard library only

### Benchmark Runner

- The runner must launch each workload via `subprocess.Popen`, wait for the `READY` signal, then invoke `py-spy record --pid {pid} --format speedscope --output {output_path}` for a configurable duration
- After py-spy exits, the runner must collect: workload wall-clock time with py-spy attached, workload wall-clock time without py-spy (baseline run), memory RSS at start and peak (via `/proc/{pid}/status` or `psutil`)
- Overhead must be calculated as `(time_with_profiler - time_without) / time_without * 100` as a percentage
- The runner must output a JSON report containing per-workload metrics: `workload_name`, `duration_s`, `baseline_duration_s`, `overhead_pct`, `peak_memory_kb`, `sample_count`, `top_functions`

### Analysis and Regression Detection

- `analysis.py` must parse the speedscope JSON output and extract: total samples, per-function sample counts, maximum call-stack depth, and thread distribution (for threaded workloads)
- Given a `baseline.json` file, the analysis must flag regressions where:
  - Overhead percentage increased by more than 20% relative to baseline
  - Sample count decreased by more than 30% (indicating missed samples)
  - Expected functions are absent from the top-10 sampled functions
- The analysis must output a pass/fail verdict with details on any flagged regressions

### Edge Cases

- If py-spy fails to attach (e.g., permission denied), the runner must log the error and continue with remaining workloads rather than aborting
- If a workload exits before the profiling duration completes, the runner must still collect partial results
- The threaded workload must gracefully handle `KeyboardInterrupt` and join all threads within 2 seconds

## Expected Functionality

- Running `python benchmarks/runner.py` executes all four workloads, attaches py-spy to each, and produces a JSON report
- The CPU-bound workload's profiling output shows `fibonacci`, `prime_sieve`, and `matrix_multiply` among the top sampled functions
- The threaded workload's profiling output attributes samples to all 4 named threads
- Overhead for CPU-bound workloads is reported as a percentage (typically < 5% for py-spy)
- `python benchmarks/analysis.py --results results.json --baseline baseline.json` compares results and prints `PASS` if no regressions, or `FAIL` with specific regression details

## Acceptance Criteria

- The project builds successfully with `cargo build --release`
- Four distinct Python workloads (CPU, memory, I/O, threaded) are runnable independently and produce deterministic profiling shapes
- The benchmark runner attaches py-spy to each workload, collects speedscope output, and computes overhead metrics
- The analysis module parses profiling output, identifies top functions by sample count, and compares against baseline for regression detection
- The CPU-bound workload produces at least 3 distinct functions each with ≥ 10% of samples in the profiling output
- The threaded workload attributes samples across all 4 named threads
- Runner handles workload failures and py-spy attachment errors gracefully without aborting
