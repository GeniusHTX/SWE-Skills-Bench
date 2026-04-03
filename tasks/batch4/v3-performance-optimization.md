# Task: Implement a Performance Benchmark Suite with Flash Attention and HNSW Search Optimization Targets

## Background

The flash-attention repository (https://github.com/Dao-AILab/flash-attention) provides optimized attention implementations for transformers. A new Python benchmark and optimization module is needed that measures baseline attention performance, implements a Flash Attention wrapper with benchmarking to validate speedup targets (2.49x–7.47x), implements an HNSW-based vector search with benchmarks to validate search improvement targets (150x–12,500x over linear scan), and produces a comprehensive performance report comparing all configurations.

## Files to Create/Modify

- `benchmarks/attention_benchmark.py` (create) — Benchmark suite comparing standard attention vs. Flash Attention across sequence lengths and head dimensions
- `benchmarks/search_benchmark.py` (create) — Benchmark suite comparing linear search vs. HNSW index search across dataset sizes
- `benchmarks/memory_benchmark.py` (create) — Memory usage profiler comparing standard vs. optimized implementations
- `benchmarks/report_generator.py` (create) — Generates performance reports with speedup calculations and target validation
- `benchmarks/__init__.py` (create) — Package init
- `tests/test_v3_performance_optimization.py` (create) — Tests for benchmark correctness and report generation

## Requirements

### Attention Benchmark (attention_benchmark.py)

- `AttentionBenchmark` class accepting: `device` (str, default `"cuda"` if available else `"cpu"`), `dtype` (torch.float16 or torch.float32)
- `standard_attention(q, k, v) -> Tensor` — computes `softmax(QK^T / sqrt(d_k)) V` using standard PyTorch operations
- `flash_attention(q, k, v) -> Tensor` — wraps the flash_attn library's `flash_attn_func` (or falls back to a memory-efficient implementation if unavailable)
- `benchmark_attention(batch_size, num_heads, seq_lengths, head_dim, num_runs=100) -> list[dict]` — for each sequence length, benchmarks both implementations and returns:
  - `{"seq_length": int, "standard_ms": float, "flash_ms": float, "speedup": float, "output_matches": bool}`
- `seq_lengths` variants to test: `[128, 256, 512, 1024, 2048, 4096]`
- Output correctness: the Flash and standard attention outputs must match within a tolerance of 1e-2 (for float16)
- Must configure CUDA synchronization for accurate GPU timing (`torch.cuda.synchronize()` before/after)

### Search Benchmark (search_benchmark.py)

- `SearchBenchmark` class accepting: `dimension` (int, default 128)
- `linear_search(query, dataset, k=10) -> tuple[list[int], float]` — brute-force k-NN returning (indices, time_ms)
- `hnsw_search(query, index, k=10) -> tuple[list[int], float]` — HNSW search returning (indices, time_ms)
- `build_hnsw_index(dataset, M=16, ef_construction=200) -> object` — builds an HNSW index (using `hnswlib` or `faiss`)
- `benchmark_search(dataset_sizes, num_queries=100, k=10) -> list[dict]` — for each dataset size, benchmarks both methods:
  - `{"dataset_size": int, "linear_ms": float, "hnsw_ms": float, "speedup": float, "recall_at_k": float}`
- `dataset_sizes` to test: `[1_000, 10_000, 100_000, 1_000_000]`
- Recall@k must be ≥ 0.95 for the HNSW search to be considered valid
- Vectors must be generated randomly with a fixed seed for reproducibility

### Memory Benchmark (memory_benchmark.py)

- `MemoryBenchmark` class
- `measure_attention_memory(batch_size, num_heads, seq_length, head_dim) -> dict` — returns `{"standard_mb": float, "flash_mb": float, "reduction_percent": float}`
- `measure_search_memory(dataset_size, dimension) -> dict` — returns `{"linear_mb": float, "hnsw_mb": float, "overhead_mb": float}`
- Memory measurement must use `torch.cuda.max_memory_allocated()` for GPU attention and `tracemalloc` for search
- Must reset memory state between measurements to ensure accuracy

### Report Generator (report_generator.py)

- `PerformanceReport` class accepting results from all three benchmarks
- `generate(attention_results, search_results, memory_results) -> dict` — produces:
  - `"attention_summary"`: mean speedup, max speedup, speedup by seq_length, target met (2.49x–7.47x)
  - `"search_summary"`: mean speedup, max speedup, speedup by dataset_size, target met (150x–12,500x)
  - `"memory_summary"`: mean reduction %, max reduction %, target met (50–75%)
  - `"overall_targets_met"`: bool — True only if all three targets met
  - `"recommendations"`: list of strings for unmet targets
- `to_markdown() -> str` — formatted markdown report with tables and pass/fail indicators
- `to_json() -> str` — JSON serialized report

### Expected Functionality

- Attention benchmark at seq_length=2048 with Flash Attention shows ≥2x speedup over standard attention on GPU
- Search benchmark at dataset_size=100,000 with HNSW shows ≥100x speedup over linear search
- Memory benchmark shows Flash Attention using significantly less memory at seq_length=4096
- The report clearly shows which targets are met and which need improvement
- On CPU-only systems, benchmarks run without error but speedup targets may not be met (report shows results regardless)

## Acceptance Criteria

- Attention benchmark correctly measures standard and Flash Attention latency with CUDA synchronization
- Output correctness validation confirms both implementations produce matching results within tolerance
- Search benchmark correctly measures linear vs. HNSW search with recall@k validation
- Memory benchmark accurately captures peak memory usage for both attention and search operations
- Report generator aggregates all results and validates against the specified performance targets
- CPU fallback mode runs all benchmarks without errors when CUDA is unavailable
- Tests verify benchmark measurement logic, report calculations, and target validation
