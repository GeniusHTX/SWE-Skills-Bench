# Task: Benchmark and Optimize FAISS Index Configurations for a Million-Vector Dataset

## Background

FAISS (https://github.com/facebookresearch/faiss) is Facebook's library for efficient similarity search. This task requires building a Python benchmarking suite that evaluates different FAISS index configurations (Flat, IVF, HNSW, PQ, IVF+PQ) on a synthetic 1-million-vector dataset, measuring recall@k, query latency, memory usage, and build time. The suite should produce a comparison report identifying the optimal index for a given recall/latency tradeoff.

## Files to Create/Modify

- `benchs/index_benchmark.py` (create) — Benchmark harness: generates synthetic data, builds multiple index configurations, runs queries, and measures metrics.
- `benchs/index_configs.py` (create) — Index configuration definitions: factory strings, build parameters, and search parameters for each index type.
- `benchs/report_generator.py` (create) — Report generator: takes benchmark results and produces a Markdown comparison table and a recommendation based on configurable recall/latency thresholds.
- `tests/test_index_benchmark.py` (create) — Tests for the benchmark harness using small-scale data (10K vectors) to validate correctness of metrics.

## Requirements

### Data Generation

- Generate `N=1,000,000` vectors of dimension `D=128` using `numpy.random.default_rng(seed=42).standard_normal((N, D)).astype('float32')`.
- Generate `Q=10,000` query vectors of same dimension.
- Compute ground-truth k-nearest neighbors using a `faiss.IndexFlatL2` brute-force index with `k=100`.

### Index Configurations

Define the following configurations in `index_configs.py`:

| Name | Factory String | nprobe / efSearch | Notes |
|------|---------------|-------------------|-------|
| Flat | `Flat` | N/A | Exact search baseline |
| IVF4096 | `IVF4096,Flat` | nprobe=16, 64, 256 | Inverted file with varying probe counts |
| HNSW32 | `HNSW32` | efSearch=32, 64, 128 | Graph-based approximate search |
| PQ32 | `PQ32` | N/A | Product quantization (32 subquantizers) |
| IVF4096_PQ32 | `IVF4096,PQ32` | nprobe=16, 64 | Combined IVF + PQ |

### Benchmark Metrics

For each configuration and parameter set, measure:
- **Build time** (seconds): time to train (if needed) and add all vectors.
- **Query latency**: median and P99 latency for single-query mode over all Q queries.
- **Recall@10**: fraction of true 10-nearest neighbors found in the approximate result.
- **Recall@100**: fraction of true 100-nearest neighbors found.
- **Memory usage** (MB): estimated from `index.sa_code_size()` × N / 1e6 where available, or `sys.getsizeof` fallback.

### Report Generator

- `generate_report(results)` → Markdown string with:
  - Table comparing all configurations: name, build time, median latency, P99 latency, recall@10, recall@100, memory.
  - `recommend(min_recall=0.95, max_latency_ms=1.0)` → returns the configuration name that achieves at least `min_recall` recall@10 with median latency ≤ `max_latency_ms`, minimizing memory. If no config satisfies both, return the one closest to the requirements.

### Expected Functionality

- `Flat` index achieves recall@10 = 1.0 but highest latency.
- `IVF4096` with nprobe=256 achieves recall@10 > 0.98 with lower latency than Flat.
- `HNSW32` with efSearch=128 achieves recall@10 > 0.99.
- `PQ32` has the smallest memory footprint but lower recall.
- `recommend(min_recall=0.95, max_latency_ms=1.0)` should suggest `HNSW32` or `IVF4096` depending on parameter settings.

## Acceptance Criteria

- The benchmark generates 1M vectors, builds all 5 index types, and measures all specified metrics.
- Ground-truth is computed with exact search and used correctly for recall calculations.
- Each index configuration uses the FAISS index factory with correct parameters.
- The report table includes all metrics for all configurations.
- The `recommend` function correctly filters and ranks configurations by the given thresholds.
- Tests validate recall computation logic, metric collection, and report format using a 10K-vector subset.
