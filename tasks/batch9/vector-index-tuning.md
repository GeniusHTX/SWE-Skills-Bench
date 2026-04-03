# Task: Implement Adaptive HNSW Parameter Tuning Benchmarks for FAISS

## Background

FAISS (https://github.com/facebookresearch/faiss) is a library for efficient similarity search. A new benchmarking module is needed that systematically tunes HNSW index parameters (M, efConstruction, efSearch), adds product quantization (PQ) for memory reduction, and produces a Pareto frontier of recall vs. latency tradeoffs. The module must also implement an adaptive tuning algorithm that automatically finds near-optimal parameters for a given dataset.

## Files to Create/Modify

- `benchs/hnsw_tuning/benchmark.py` (create) — `HNSWBenchmark` class that builds HNSW indexes with varying parameters, measures recall@k and query latency, and records results
- `benchs/hnsw_tuning/adaptive_tuner.py` (create) — `AdaptiveTuner` class that uses binary search on efSearch and grid search on M/efConstruction to find parameter configurations meeting target recall with minimal latency
- `benchs/hnsw_tuning/quantization.py` (create) — `QuantizationBenchmark` class that compares HNSW with HNSW+PQ and HNSW+SQ (scalar quantization) for memory-latency-recall tradeoffs
- `benchs/hnsw_tuning/report.py` (create) — Report generator that outputs benchmark results as CSV and produces a Pareto frontier analysis identifying non-dominated configurations
- `benchs/hnsw_tuning/run_benchmark.py` (create) — CLI entry point that generates synthetic data and runs all benchmarks
- `tests/test_hnsw_tuning.py` (create) — Tests verifying recall calculation correctness, Pareto frontier logic, and adaptive tuner convergence

## Requirements

### Benchmark (`benchmark.py`)

- Class `HNSWBenchmark` accepts: `vectors` (np.ndarray, shape [N, D]), `queries` (np.ndarray, shape [Q, D]), `ground_truth` (np.ndarray, shape [Q, K], indices of true K nearest neighbors for each query), `k` (int, default 10)
- Method `build_index(M: int, efConstruction: int) -> faiss.IndexHNSWFlat` — Creates and populates an HNSW index with the given parameters
- Method `search(index: faiss.IndexHNSWFlat, efSearch: int) -> tuple[np.ndarray, float]` — Sets `index.hnsw.efSearch = efSearch`, searches all queries, returns `(result_indices, avg_latency_ms)`
- Method `compute_recall(result_indices: np.ndarray) -> float` — Recall@K: fraction of true neighbors found in the result set across all queries
- Method `run_grid(m_values, ef_construction_values, ef_search_values) -> pd.DataFrame` — Runs all parameter combinations, returns DataFrame with columns: `M`, `efConstruction`, `efSearch`, `recall`, `latency_ms`, `index_size_mb`, `build_time_s`
- Index size computed via `faiss.serialize_index(index)` byte length / 1e6

### Adaptive Tuner (`adaptive_tuner.py`)

- Class `AdaptiveTuner` accepts: `benchmark` (HNSWBenchmark instance), `target_recall` (float, default 0.95), `max_latency_ms` (float, default 10.0)
- Method `tune() -> dict` — Returns `{"M": int, "efConstruction": int, "efSearch": int, "recall": float, "latency_ms": float}`:
  1. For each M in [8, 16, 32, 48, 64], build index with efConstruction = M * 8
  2. For each built index, binary search efSearch in [16, 512] to find the minimum efSearch achieving `target_recall`
  3. Among configurations meeting target_recall, select the one with lowest latency
  4. If no configuration meets target_recall, return the one with highest recall
- Binary search must converge within 10 iterations
- Must log each step's parameters and results for debugging

### Quantization Benchmark (`quantization.py`)

- Class `QuantizationBenchmark` accepts: `vectors`, `queries`, `ground_truth`, `k`, `M` (int), `efConstruction` (int)
- Method `benchmark_flat() -> dict` — Baseline HNSW with full-precision vectors; returns `{"type": "HNSW_Flat", "recall": float, "latency_ms": float, "memory_mb": float}`
- Method `benchmark_pq(nbits: int = 8, M_pq: int = 16) -> dict` — HNSW with product quantization (`faiss.IndexHNSWPQ`); returns same format with `"type": "HNSW_PQ"`
- Method `benchmark_sq(qtype: int = faiss.ScalarQuantizer.QT_8bit) -> dict` — HNSW with scalar quantization (`faiss.IndexHNSWSQ`); returns same format with `"type": "HNSW_SQ"`
- Method `compare_all(ef_search: int) -> pd.DataFrame` — Runs all three methods and returns comparison DataFrame

### Report (`report.py`)

- Function `pareto_frontier(results: pd.DataFrame, x_col: str = "latency_ms", y_col: str = "recall") -> pd.DataFrame` — Returns only non-dominated configurations (no other config has both better recall AND lower latency)
- Function `save_report(results: pd.DataFrame, pareto: pd.DataFrame, output_dir: str)` — Saves `full_results.csv`, `pareto_frontier.csv` to the output directory

### Expected Functionality

- Grid search with M=[16,32], efConstruction=[64,128], efSearch=[32,64,128] produces 12 result rows
- Pareto frontier of 12 results contains 2–5 non-dominated configurations
- Adaptive tuner with target_recall=0.95 converges to a configuration achieving ≥0.95 recall on standard benchmarks (sift-like data)
- PQ index uses 3–10x less memory than flat index with recall > 0.85
- SQ index uses ~4x less memory than flat index with recall > 0.90

## Acceptance Criteria

- `HNSWBenchmark` correctly builds FAISS HNSW indexes and measures recall@K
- Recall computation matches: `sum(intersection(result[i], gt[i]) for all i) / (Q * K)`
- Adaptive tuner converges within 10 binary search iterations per M value
- Quantization benchmarks produce valid `IndexHNSWPQ` and `IndexHNSWSQ` indexes
- Pareto frontier correctly identifies non-dominated solutions
- `cmake -B build && cmake --build build` compiles FAISS
- `python -m pytest /workspace/tests/test_vector_index_tuning.py -v --tb=short` passes
