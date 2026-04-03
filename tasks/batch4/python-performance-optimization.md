# Task: Build a Python Performance Profiling and Optimization Toolkit for py-spy

## Background

The py-spy repository (https://github.com/benfred/py-spy) is a sampling profiler for Python. A new Python companion module is needed that provides programmatic profiling utilities: a decorator-based CPU profiler, a memory tracker, a benchmark suite for comparing implementations, a bottleneck detector that identifies hotspots, and optimization helpers (memoization, lazy evaluation, batch processing) — enabling developers to profile and optimize Python code systematically.

## Files to Create/Modify

- `examples/profiling_toolkit/profiler.py` (create) — CPU profiler decorator and context manager using cProfile with formatted output
- `examples/profiling_toolkit/memory_tracker.py` (create) — Memory usage tracker with peak detection and allocation timeline
- `examples/profiling_toolkit/benchmark.py` (create) — Benchmark suite for comparing function performance with statistical analysis
- `examples/profiling_toolkit/optimizer.py` (create) — Optimization utilities: memoize, lazy_property, batch_processor, chunk_iterator
- `examples/profiling_toolkit/__init__.py` (create) — Package init
- `tests/test_python_performance_optimization.py` (create) — Tests for all profiling and optimization utilities

## Requirements

### CPU Profiler (profiler.py)

- `@profile(sort_by="cumulative", top_n=20)` decorator — profiles the decorated function using `cProfile.Profile`, prints the top N functions sorted by the specified key, returns the original function's result
- `ProfileContext(sort_by="cumulative", top_n=20)` context manager — profiles a block of code; accessible via `with ProfileContext() as p:` and `p.stats` after the block
- `profile_to_file(func, output_path, *args, **kwargs)` — profiles the function call and writes the result to a `.prof` file readable by `pstats` or visualization tools
- `compare_profiles(func_a, func_b, args=(), kwargs={}, runs=100) -> dict` — profiles both functions over multiple runs and returns `{"func_a": {"mean_time": float, "std_time": float}, "func_b": {...}, "speedup": float, "winner": str}`
- Timing must use `time.perf_counter_ns()` for nanosecond precision

### Memory Tracker (memory_tracker.py)

- `@track_memory` decorator — measures memory before and after function execution; prints peak memory, delta, and allocations; returns the function's result
- `MemorySnapshot` class:
  - `take() -> dict` — captures current memory usage: `rss_mb`, `vms_mb`, `percent`
  - `compare(other: MemorySnapshot) -> dict` — returns delta between two snapshots
- `track_allocations(func, *args, **kwargs) -> dict` — runs the function and returns `{"peak_mb": float, "delta_mb": float, "duration_s": float, "result": Any}`
- Must use `tracemalloc` for allocation tracking and `psutil.Process().memory_info()` for RSS measurements
- If `psutil` is not available, fall back to `tracemalloc` only (no RSS) without raising

### Benchmark Suite (benchmark.py)

- `Benchmark` class accepting `name` (str)
- `add(name: str, func: callable, args=(), kwargs={})` — registers a function to benchmark
- `run(iterations=1000, warmup=100) -> BenchmarkResult` — runs each function for `warmup` iterations (discarded), then `iterations` measured runs
- `BenchmarkResult` properties:
  - `results` — dict of name → `{"mean_ns": int, "std_ns": int, "min_ns": int, "max_ns": int, "median_ns": int, "iterations": int}`
  - `fastest` — name of the fastest function
  - `comparison_table() -> str` — formatted ASCII table with columns: Name, Mean, Std, Min, Max, Relative
  - `to_dict() -> dict` — serializable dictionary
- Statistical outlier removal: discard runs beyond 2 standard deviations before computing final stats

### Optimization Utilities (optimizer.py)

- `@memoize(maxsize=128)` — LRU cache decorator wrapping `functools.lru_cache` with added `cache_info()` and `cache_clear()` methods on the wrapped function; supports unhashable arguments by falling back to a dict-based cache keyed by `repr(args)`
- `@lazy_property` — descriptor that computes a property value on first access and caches it on the instance
- `batch_processor(items, batch_size, process_fn) -> list` — processes items in batches, calling `process_fn(batch)` for each batch; returns flattened results
- `chunk_iterator(iterable, chunk_size) -> Iterator` — yields chunks of `chunk_size` from the iterable; last chunk may be smaller
- `@timed(label=None)` — decorator that logs execution time using `logging.info`; `label` defaults to the function name

### Expected Functionality

- `@profile` on a function that sums 1M numbers prints a cProfile table and returns the sum
- `compare_profiles(list_comp, generator_expr, runs=1000)` shows which approach is faster with speedup factor
- `@track_memory` on a function that creates a large list shows ~76 MB delta for 10M integers
- A benchmark comparing `sorted()` vs. `list.sort()` shows relative performance with statistical confidence
- `@memoize` on a recursive Fibonacci function reduces O(2^n) to O(n) call time
- `batch_processor(range(100), 10, process)` calls `process` 10 times with batches of 10

## Acceptance Criteria

- CPU profiler decorator and context manager correctly measure and display cProfile statistics
- Profile comparison runs both functions multiple times and reports mean, std, and speedup
- Memory tracker reports peak RSS, delta, and allocation counts for profiled functions
- Benchmark suite produces statistically sound results with warmup, outlier removal, and comparison tables
- Memoize handles both hashable and unhashable arguments with LRU eviction
- Lazy property computes once and caches on the instance
- Batch processor and chunk iterator correctly partition items
- Tests verify profiling output, memory tracking, benchmark statistics, and optimization correctness
