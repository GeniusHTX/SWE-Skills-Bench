# Task: Implement Flash Attention Benchmark Suite and HNSW Search Performance Validator

## Background

The `Dao-AILab/flash-attention` repository provides optimized attention kernels. A benchmark module is needed that measures Flash Attention v2/v3 speedup over standard PyTorch attention, validates memory usage reduction targets, and benchmarks HNSW-based vector search against linear scan — producing structured JSON results that can be consumed by CI to enforce performance regression gates.

## Files to Create/Modify

- `benchmarks/benchmark_flash_attn_v3.py` (create) — Benchmark script measuring wall-clock time and peak GPU memory for Flash Attention vs. standard `torch.nn.functional.scaled_dot_product_attention` across sequence lengths `[512, 1024, 2048, 4096]` and head dimensions `[64, 128]`
- `benchmarks/benchmark_hnsw_search.py` (create) — Benchmark script comparing HNSW approximate nearest-neighbor search against brute-force cosine similarity search on a 1M-vector dataset at dimensions `[128, 256, 512]`
- `benchmarks/perf_validator.py` (create) — Module with `validate_results(results_path: str, thresholds_path: str) -> ValidationReport` that reads JSON benchmark outputs and checks each metric against defined thresholds
- `benchmarks/thresholds.json` (create) — JSON thresholds file specifying: flash attention speedup ≥ 2.0x for all tested configs, memory reduction ≥ 40%, HNSW search speedup ≥ 100x over brute-force at 1M vectors
- `tests/test_perf_validator.py` (create) — Unit tests for `validate_results` covering passing results, a failing speedup threshold, a failing memory threshold, and malformed JSON input

## Requirements

### Flash Attention Benchmark

- Use `torch.cuda.Event` for GPU timing (not `time.time()`); record 10 warmup iterations then 50 timed iterations; report median and P95 latency
- For each configuration `(batch=4, heads=16, seq_len, head_dim)` test both causal and non-causal attention
- Compute peak GPU memory via `torch.cuda.max_memory_allocated()` before and after each run; reset with `torch.cuda.reset_peak_memory_stats()` between runs
- Output a JSON file `benchmarks/results/flash_attn_results.json` with schema:
  ```json
  {
    "configs": [
      {
        "seq_len": 1024,
        "head_dim": 64,
        "causal": true,
        "flash_attn_median_ms": 1.23,
        "baseline_median_ms": 4.56,
        "speedup": 3.70,
        "flash_attn_peak_mem_mb": 120.5,
        "baseline_peak_mem_mb": 280.0,
        "memory_reduction_pct": 56.9
      }
    ]
  }
  ```
- If CUDA is not available at runtime, the script must print `"CUDA not available, skipping GPU benchmarks"` and exit with code 0 (not code 1)

### HNSW Search Benchmark

- Generate a random float32 dataset of shape `(1_000_000, dim)` for each tested dimension
- Use `faiss.IndexHNSWFlat` with `M=32` and `efSearch=64` for HNSW; use `faiss.IndexFlatIP` for brute-force baseline
- Measure query time for 1000 random query vectors; report median query time in ms and recall@10 (fraction of true top-10 results in HNSW results)
- Output `benchmarks/results/hnsw_results.json` with per-dimension results including `median_query_ms_hnsw`, `median_query_ms_brute`, `speedup`, `recall_at_10`

### Validation Logic

- `ValidationReport` dataclass must contain: `passed: bool`, `failures: list[str]`, `warnings: list[str]`
- For each metric in `thresholds.json`, if the measured value fails the threshold, append a descriptive failure string to `failures`
- If the flash attention speedup is ≥ threshold but the memory reduction is < threshold, append a `warning` but do not set `passed = False` — memory reduction is a soft target
- `validate_results` must raise `FileNotFoundError` if either `results_path` or `thresholds_path` does not exist
- `validate_results` must raise `ValueError` with a descriptive message if either file contains invalid JSON

### Expected Functionality

- Results where all speedups ≥ 2.0x and all memory reductions ≥ 40% → `report.passed = True`, `report.failures = []`
- Results where speedup for seq_len=4096 is 1.8x (below 2.0x threshold) → `report.passed = False`, `report.failures` contains a string mentioning `"seq_len=4096"` and `"speedup"`
- Memory reduction at 35% (below 40%) → `report.warnings` contains a string mentioning `"memory_reduction"`, but `report.passed` may still be True if all speedup thresholds pass
- Passing a file path that does not exist → raises `FileNotFoundError`
- Passing a file with `{"broken": }` content → raises `ValueError`

## Acceptance Criteria

- `pip install -e . && python -c 'import flash_attn'` exits with code 0
- `benchmarks/benchmark_flash_attn_v3.py` runs on a CUDA-capable machine and produces `benchmarks/results/flash_attn_results.json` with one entry per `(seq_len, head_dim, causal)` combination
- `benchmarks/benchmark_hnsw_search.py` produces `benchmarks/results/hnsw_results.json` with entries for all three tested dimensions
- `validate_results` returns `passed=True` for the threshold file `benchmarks/thresholds.json` when results meet all minimums
- `validate_results` returns `passed=False` with a non-empty `failures` list when any speedup threshold is not met
- Unit tests in `tests/test_perf_validator.py` cover all specified scenarios and pass via `python -m pytest tests/test_perf_validator.py -v`
