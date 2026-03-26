# Task: Implement HNSW Index Parameter Tuning and Quantization Benchmarks for FAISS

## Background

FAISS (https://github.com/facebookresearch/faiss) is Facebook AI's library for efficient similarity search and clustering of dense vectors. The project needs a benchmarking module that systematically tunes HNSW index parameters, evaluates quantization strategies (PQ, SQ, OPQ), and produces comparison reports showing the recall-latency-memory tradeoff across configurations.

## Files to Create/Modify

- `benchs/hnsw_tuning.py` (create) — HNSW parameter tuning benchmark: varying M, efConstruction, efSearch
- `benchs/quantization_benchmark.py` (create) — Quantization strategy evaluation: PQ, SQ8, OPQ
- `benchs/index_selector.py` (create) — Index recommendation engine based on dataset characteristics
- `benchs/benchmark_report.py` (create) — Report generator for benchmark results
- `tests/test_hnsw_tuning.py` (create) — Tests for benchmark correctness

## Requirements

### HNSW Parameter Tuning

- Implement a `HNSWTuner` class that benchmarks HNSW index performance across parameter combinations:
  - `M` values: [8, 16, 32, 64]
  - `efConstruction` values: [40, 100, 200, 400]
  - `efSearch` values: [16, 32, 64, 128, 256]
- For each combination, measure: build time (seconds), index size (bytes), query latency (ms, averaged over 1000 queries), recall@1, recall@10, recall@100
- Recall is computed against brute-force exact search results (ground truth from `IndexFlatL2`)
- Accept configurable dataset: `num_vectors` (int), `dimension` (int), `num_queries` (int, default 1000)
- Generate random float32 vectors using numpy for benchmarking (controlled random seed for reproducibility)

### Quantization Benchmarks

- Benchmark three quantization strategies applied to HNSW:
  - **PQ (Product Quantization)**: `IndexHNSWPQ` with configurable `M_pq` (number of subquantizers) and `nbits` (bits per code, default 8)
  - **SQ (Scalar Quantization)**: `IndexHNSWSQ` with `QT_8bit` and `QT_4bit` quantizer types
  - **OPQ (Optimized Product Quantization)**: `OPQMatrix` + `IndexHNSWPQ` with rotation matrix optimization
- For each strategy, measure: index size, build time, query latency, recall@10
- Compute the **compression ratio**: `original_size / index_size`
- Compare all strategies on the same dataset

### Index Recommendation Engine

- Implement `recommend_index(num_vectors, dimension, recall_target, latency_target_ms, memory_budget_mb)` that returns the best index configuration:
  - If `num_vectors < 100_000`: recommend `IndexFlatL2` (brute force) — simplest, exact
  - If `num_vectors < 1_000_000` and `recall_target > 0.95`: recommend `IndexHNSWFlat` with `M=32`, `efConstruction=200`
  - If `num_vectors < 1_000_000` and `memory_budget_mb` is tight: recommend `IndexHNSWSQ` with `QT_8bit`
  - If `num_vectors >= 1_000_000`: recommend `IndexIVFPQ` with `nlist=int(sqrt(num_vectors))`, `M_pq=dimension//4`, `nprobe=max(1, nlist//10)`
  - If `num_vectors >= 10_000_000` and memory is constrained: recommend `IndexIVFPQ` with `OPQMatrix` preprocessing
- Return a `Recommendation` containing: `index_type` (string), `parameters` (dict), `estimated_memory_mb` (float), `reasoning` (string)
- HNSW estimated memory: `num_vectors * (dimension * 4 + M * 8 + 16)` bytes
- IVF-PQ estimated memory: `num_vectors * (M_pq * nbits / 8 + 8)` bytes

### Benchmark Report

- Implement `BenchmarkReport` class that generates comparison reports:
  - `add_result(config_name, metrics)` — add a benchmark result
  - `generate_table()` — produce a formatted comparison table (string, tabular format)
  - `pareto_frontier()` — identify Pareto-optimal configurations (not dominated by any other in both recall and latency)
  - `to_csv(path)` — export results to CSV
  - `to_json()` — export results to JSON (deterministic, sorted keys)
- Pareto frontier: a configuration A dominates B if A has better recall AND lower latency; Pareto-optimal configs are those not dominated by any other

### Expected Functionality

- `HNSWTuner` with M=[16, 32], efConstruction=[100, 200] produces 4 configurations with measured recall and latency
- Increasing M from 16 to 32 increases recall but also increases memory and build time
- Increasing efSearch from 16 to 256 increases recall and latency
- PQ quantization reduces index size by ~4x compared to flat HNSW, with some recall loss
- `recommend_index(500_000, 128, 0.95, 10, 2048)` returns HNSW with M=32
- `recommend_index(50_000_000, 768, 0.90, 20, 8192)` returns IVF-PQ with OPQ
- Pareto frontier of 10 configurations returns 3–5 non-dominated configurations

## Acceptance Criteria

- `HNSWTuner` benchmarks all parameter combinations and reports recall@1/10/100, latency, and memory per configuration
- Recall is computed correctly against `IndexFlatL2` ground truth
- Quantization benchmarks compare PQ, SQ8, SQ4, and OPQ with correct index construction
- Compression ratio is computed correctly as original_size / index_size
- `recommend_index` returns appropriate index types and parameters for different scale/recall/memory combinations
- Estimated memory calculations match the formulas specified
- `BenchmarkReport` generates correct comparison tables and identifies Pareto-optimal configurations
- Pareto frontier algorithm correctly identifies non-dominated configurations
- CSV and JSON exports produce correct, deterministic output
- Tests verify recall computation, index recommendation logic, and Pareto frontier identification with known inputs
