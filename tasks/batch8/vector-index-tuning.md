# Task: Implement an HNSW Index Benchmarking and Tuning Module for FAISS

## Background

FAISS (https://github.com/facebookresearch/faiss) is a library for efficient similarity search and clustering of dense vectors. The project needs a Python benchmarking module that systematically evaluates HNSW index configurations to find optimal parameter combinations for a given dataset. The module must sweep HNSW construction parameters (M, efConstruction) and search parameters (efSearch), measure recall, latency, and memory usage, and produce a Pareto frontier of optimal configurations balancing recall against search speed.

## Files to Create/Modify

- `benchs/hnsw_tuner.py` (create) — `HNSWTuner` class that builds HNSW indexes with different parameter combinations, benchmarks each configuration, and identifies Pareto-optimal settings
- `benchs/quantization_evaluator.py` (create) — `QuantizationEvaluator` class comparing full-precision (FP32), scalar quantization (SQ8), and product quantization (PQ) on HNSW indexes, measuring recall degradation vs memory savings
- `benchs/benchmark_runner.py` (create) — `BenchmarkRunner` class that executes a full tuning sweep, stores results, and generates a summary report with recommendations
- `benchs/benchmark_utils.py` (create) — Utility functions: `compute_recall_at_k`, `compute_ground_truth` (brute-force exact search), `estimate_memory_bytes`, `generate_synthetic_data`
- `tests/test_vector_index_tuning.py` (create) — Tests for recall computation, parameter sweep correctness, Pareto frontier extraction, and quantization comparison

## Requirements

### Benchmark Utilities (`benchmark_utils.py`)

- `generate_synthetic_data(n_vectors: int, dimension: int, n_queries: int, seed: int = 42) -> tuple[np.ndarray, np.ndarray]` — Generate random float32 vectors (uniform [-1, 1]) for the database and queries; set `np.random.seed(seed)` for reproducibility
- `compute_ground_truth(database: np.ndarray, queries: np.ndarray, k: int) -> np.ndarray` — Use brute-force L2 distance to find exact k nearest neighbors for each query; return shape `(n_queries, k)` integer array of indices
- `compute_recall_at_k(predicted: np.ndarray, ground_truth: np.ndarray, k: int) -> float` — For each query, compute the proportion of true top-k neighbors found in the predicted top-k, then average across all queries
- `estimate_memory_bytes(n_vectors: int, dimension: int, M: int, quantization: str = "none") -> int`:
  - `"none"` (FP32): `n_vectors * (dimension * 4 + M * 2 * 8)` bytes (vector storage + graph edges)
  - `"SQ8"`: `n_vectors * (dimension * 1 + M * 2 * 8)` bytes
  - `"PQ"`: `n_vectors * (pq_bytes + M * 2 * 8)` bytes where `pq_bytes = dimension / 4 * 1` (assuming 4-dimensional subquantizers with 8 bits each)

### HNSWTuner

- Constructor: `HNSWTuner(database: np.ndarray, queries: np.ndarray, ground_truth: np.ndarray, k: int = 10)`
- `sweep(m_values: list[int] = [8, 16, 32, 64], ef_construction_values: list[int] = [40, 100, 200], ef_search_values: list[int] = [16, 32, 64, 128, 256]) -> list[dict]`:
  - For each `(M, efConstruction)` combination, build a `faiss.IndexHNSWFlat` with the given parameters
  - For each `efSearch` value, run all queries and record:
    - `recall_at_k`: float (using `compute_recall_at_k`)
    - `qps`: float (queries per second)
    - `avg_latency_ms`: float (average milliseconds per query)
    - `build_time_s`: float (seconds to build the index)
    - `memory_estimate_mb`: float (estimated memory in MB)
    - Configuration: `M`, `efConstruction`, `efSearch`
  - Return the full list of result dicts (one per configuration combination)
- `pareto_frontier(results: list[dict], x_metric: str = "avg_latency_ms", y_metric: str = "recall_at_k") -> list[dict]` — Extract the Pareto-optimal configurations where no other configuration is strictly better on both metrics; sort by `x_metric` ascending
- `recommend(target_recall: float = 0.95) -> dict` — From the Pareto frontier, return the configuration with the lowest latency that achieves at least `target_recall`; if no configuration meets the target, return the one with the highest recall and include `"target_met": False`

### QuantizationEvaluator

- Constructor: `QuantizationEvaluator(database: np.ndarray, queries: np.ndarray, ground_truth: np.ndarray, k: int = 10)`
- `compare(M: int = 32, ef_construction: int = 100, ef_search: int = 64) -> list[dict]`:
  - Build three FAISS indexes with the same HNSW graph parameters:
    - `"FP32"`: `faiss.IndexHNSWFlat(dimension, M)`
    - `"SQ8"`: `faiss.IndexHNSWSQ(dimension, faiss.ScalarQuantizer.QT_8bit, M)`
    - `"PQ"`: `faiss.IndexHNSWPQ(dimension, pq_m, M)` where `pq_m = dimension // 4` (number of subquantizers)
  - Measure recall, latency, and memory for each; return list of result dicts with `quantization_type`, `recall_at_k`, `avg_latency_ms`, `memory_estimate_mb`, `recall_degradation` (vs FP32)
- If `dimension` is not divisible by 4 for PQ, use `pq_m = max(1, dimension // 8)` and note the adjustment

### BenchmarkRunner

- Constructor: `BenchmarkRunner(n_vectors: int = 100000, dimension: int = 128, n_queries: int = 1000, k: int = 10)`
- `run_full_sweep() -> dict`:
  - Generate synthetic data, compute ground truth
  - Run HNSW parameter sweep
  - Run quantization comparison with best HNSW configuration
  - Return `{"hnsw_results": list, "pareto_frontier": list, "recommendation": dict, "quantization_comparison": list, "dataset_info": dict}`
- `run_targeted(M: int, ef_construction: int, ef_search_range: list[int]) -> dict` — Quick benchmark of a specific configuration across the ef_search range only

### Edge Cases

- `k` exceeding the number of database vectors: clamp to `n_vectors`
- Single query: `qps` is computed as `1 / latency_seconds`
- All configurations achieving the same recall: Pareto frontier contains only the one with lowest latency
- PQ with very low dimensions (< 4): fall back to SQ8 and print a warning

## Expected Functionality

- `generate_synthetic_data(100000, 128, 1000)` produces two arrays of shape `(100000, 128)` and `(1000, 128)`
- Running `HNSWTuner.sweep()` with default parameters produces 60 result dicts (4 M × 3 efConstruction × 5 efSearch)
- The Pareto frontier for recall-vs-latency contains 5-10 configurations forming a convex boundary
- `recommend(target_recall=0.95)` returns the fastest configuration with ≥95% recall
- `QuantizationEvaluator.compare()` shows SQ8 with ~1-3% recall degradation and ~75% memory reduction vs FP32

## Acceptance Criteria

- `compute_recall_at_k` returns 1.0 when predicted neighbors exactly match ground truth
- `HNSWTuner.sweep()` builds FAISS HNSW indexes with specified parameters and measures recall and latency
- `pareto_frontier()` correctly identifies non-dominated configurations
- `recommend()` returns the optimal configuration for the target recall constraint
- `QuantizationEvaluator` compares FP32, SQ8, and PQ variants and quantifies recall degradation
- `BenchmarkRunner.run_full_sweep()` executes end-to-end and produces a complete results report
- All tests pass with `pytest`
