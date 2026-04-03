# Task: Build a Flash Attention Performance Benchmarking and Optimization Suite

## Background

Flash Attention (https://github.com/Dao-AILab/flash-attention) is a fast and memory-efficient attention implementation. The project needs a comprehensive benchmarking module that measures Flash Attention's performance against standard attention across various sequence lengths, head dimensions, and batch sizes, validates the claimed speedup targets, profiles memory usage, and generates optimization recommendations based on hardware and workload characteristics.

## Files to Create/Modify

- `benchmarks/attention_benchmark.py` (create) — `AttentionBenchmark` class measuring forward and backward pass latency, memory usage, and throughput for both standard and flash attention across configurable parameter grids
- `benchmarks/memory_profiler.py` (create) — `MemoryProfiler` class tracking peak GPU memory allocation during attention operations and computing memory savings percentages
- `benchmarks/performance_analyzer.py` (create) — `PerformanceAnalyzer` class that processes benchmark results, computes speedup ratios, identifies optimal configurations, and generates Pareto frontiers for latency-vs-memory trade-offs
- `benchmarks/benchmark_report.py` (create) — `BenchmarkReport` class producing structured benchmark reports with summary statistics, per-configuration breakdowns, and optimization recommendations
- `tests/test_v3_performance_optimization.py` (create) — Tests for benchmark measurement logic, speedup calculations, memory profiling, and report generation

## Requirements

### AttentionBenchmark

- Constructor: `AttentionBenchmark(device: str = "cuda", dtype: str = "float16", warmup_iters: int = 10, bench_iters: int = 100)`
- `benchmark_standard_attention(batch_size: int, seq_len: int, n_heads: int, head_dim: int) -> dict`:
  - Compute standard scaled dot-product attention: `softmax(QK^T / sqrt(d)) × V`
  - Measure forward pass latency (median over `bench_iters` after `warmup_iters` warmup)
  - Measure backward pass latency (same methodology)
  - Return `{"forward_ms": float, "backward_ms": float, "total_ms": float, "peak_memory_mb": float, "flops": int}`
  - FLOPs calculation: `4 × batch_size × n_heads × seq_len² × head_dim` (2 for QK^T matmul, 2 for attn×V matmul)
- `benchmark_flash_attention(batch_size: int, seq_len: int, n_heads: int, head_dim: int, causal: bool = False) -> dict`:
  - Use flash_attn's `flash_attn_func` or `flash_attn_qkvpacked_func`
  - Same measurements and return format as standard attention, plus `causal` flag in output
- `sweep(batch_sizes: list[int], seq_lengths: list[int], n_heads: list[int], head_dims: list[int], causal: bool = False) -> list[dict]`:
  - Run both standard and flash attention for every parameter combination
  - Each result dict includes the configuration, both benchmark results, and `speedup_forward`, `speedup_backward`, `memory_savings_pct`
  - Skip configurations where standard attention would exceed available GPU memory (catch OOM errors and record `"standard_oom": True`)
- If CUDA is not available, raise `RuntimeError("CUDA device required for attention benchmarks")`

### MemoryProfiler

- Constructor: `MemoryProfiler(device: str = "cuda")`
- `profile_operation(fn: Callable, *args, **kwargs) -> dict`:
  - Reset peak memory stats, run the function, record peak memory
  - Return `{"peak_memory_mb": float, "allocated_mb": float, "reserved_mb": float}`
- `compare_memory(standard_fn: Callable, flash_fn: Callable, **shared_kwargs) -> dict`:
  - Profile both functions and return `{"standard_peak_mb": float, "flash_peak_mb": float, "savings_mb": float, "savings_pct": float}`
  - `savings_pct = (standard - flash) / standard × 100`; if standard is 0, return 0.0
- `estimate_memory(batch_size: int, seq_len: int, n_heads: int, head_dim: int, dtype_bytes: int = 2) -> dict`:
  - Standard attention: `QKV storage + attention matrix + output = 3 × B × H × S × D × dtype + B × H × S × S × dtype + B × H × S × D × dtype` bytes
  - Flash attention (approximate): `QKV storage + output = 3 × B × H × S × D × dtype + B × H × S × D × dtype` bytes (no S×S matrix)
  - Return `{"standard_mb": float, "flash_mb": float, "savings_pct": float}`

### PerformanceAnalyzer

- Constructor: `PerformanceAnalyzer(results: list[dict])` where `results` is the output of `AttentionBenchmark.sweep()`
- `compute_speedup_summary() -> dict`:
  - `min_speedup`: float (minimum forward speedup across all configs)
  - `max_speedup`: float (maximum forward speedup)
  - `mean_speedup`: float (average forward speedup)
  - `median_speedup`: float
  - `speedup_by_seq_len`: dict mapping seq_len to mean speedup (larger sequences should show more speedup)
  - `speedup_by_head_dim`: dict mapping head_dim to mean speedup
- `pareto_frontier(x_metric: str = "total_ms", y_metric: str = "peak_memory_mb") -> list[dict]` — Return flash attention configurations that are not dominated by any other configuration on both metrics
- `find_crossover_point(head_dim: int = 64, n_heads: int = 8, batch_size: int = 1) -> int` — Find the minimum sequence length where flash attention becomes faster than standard attention (binary search between 32 and 8192); return the sequence length, or -1 if flash is always slower or always faster in the range
- `optimal_config(constraint: str = "latency", max_memory_mb: float = None) -> dict`:
  - `"latency"`: Return the flash attention config with the lowest total_ms
  - `"memory"`: Return the config with the lowest peak_memory_mb
  - `"balanced"`: Return the Pareto-optimal config closest to the origin when both metrics are normalized to [0, 1]
  - If `max_memory_mb` is specified, filter to configs within that memory budget first

### BenchmarkReport

- Constructor: `BenchmarkReport(analyzer: PerformanceAnalyzer, sweep_results: list[dict])`
- `generate() -> dict` with sections:
  - `summary`: Speedup summary from analyzer
  - `memory_analysis`: Memory savings by configuration
  - `scaling_analysis`: How speedup changes with sequence length (should increase)
  - `recommendations`: List of str recommendations based on results (e.g., "Use Flash Attention for sequences > 512 tokens where speedup exceeds 2x")
  - `configurations`: Total configs tested, how many had OOM, best/worst configs
- `to_markdown() -> str` — Render the report as a Markdown document with tables and bullet points
- Recommendations rules:
  - If `mean_speedup > 2.0`: `"Flash Attention provides significant speedup (>{mean_speedup:.1f}x mean). Recommended for all configurations."`
  - If crossover point found: `"Flash Attention becomes faster at sequence length {crossover}+. Use standard attention for shorter sequences."`
  - If memory savings > 50% at max seq_len: `"Flash Attention enables {savings:.0f}% memory reduction at sequence length {max_seq_len}, allowing larger batch sizes or longer sequences."`

### Edge Cases

- Standard attention OOM at long sequences: record `"standard_oom": True`, compute speedup as `float('inf')` for those configs, exclude from summary statistics
- All configs OOM for standard attention: report section notes "Standard attention could not run for any configuration"
- Zero warmup iterations: skip warmup, proceed directly to benchmark
- Single iteration benchmark: median equals that single measurement

## Expected Functionality

- `AttentionBenchmark.sweep(batch_sizes=[1,4], seq_lengths=[512,1024,2048], n_heads=[8], head_dims=[64])` produces 6 configuration results with speedup ratios
- Flash attention shows increasing speedup as sequence length grows (e.g., 1.5x at 512, 2.5x at 1024, 4x at 2048)
- `MemoryProfiler.estimate_memory(1, 2048, 8, 64)` shows standard attention requiring ~512MB (including S×S attention matrix) vs flash attention requiring ~96MB
- `PerformanceAnalyzer.find_crossover_point()` returns ~256-512 depending on hardware
- `BenchmarkReport.to_markdown()` produces a formatted report with tables and specific recommendations

## Acceptance Criteria

- `AttentionBenchmark` correctly measures forward/backward latency for both standard and flash attention implementations
- Speedup ratios are computed as `standard_ms / flash_ms` for each configuration
- `MemoryProfiler` accurately tracks peak GPU memory and computes savings percentages
- `PerformanceAnalyzer` identifies Pareto-optimal configurations and finds the sequence-length crossover point
- `BenchmarkReport` generates structured reports with data-driven recommendations
- OOM errors during standard attention benchmarks are caught and recorded without crashing
- All tests pass with `pytest`
