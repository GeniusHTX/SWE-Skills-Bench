# Task: Implement Adaptive HNSW Index Tuner for FAISS

## Background

The FAISS library (https://github.com/facebookresearch/faiss) provides efficient similarity search and clustering. A new Python module is needed that automates HNSW index parameter tuning by benchmarking different parameter combinations against user-specified recall and latency targets, selecting optimal configurations, and supporting product quantization for memory-constrained deployments.

## Files to Create/Modify

- `contrib/hnsw_tuner.py` (create) — `HNSWTuner` class that benchmarks parameter combinations and recommends optimal settings
- `contrib/quantization_advisor.py` (create) — `QuantizationAdvisor` class that recommends and applies quantization based on memory and recall constraints
- `tests/test_hnsw_tuner.py` (create) — Tests using synthetic datasets to verify tuning logic

## Requirements

### HNSWTuner Class

- Constructor accepts: `vectors` (numpy array, shape `(n, d)`), `queries` (numpy array, shape `(q, d)`), `ground_truth` (numpy array of true k-nearest neighbor IDs, shape `(q, k)`), `metric` (one of `"L2"`, `"IP"`, default `"L2"`)
- `benchmark(m_values, ef_construction_values, ef_search_values)` — builds an HNSW index for each `(M, efConstruction)` pair and evaluates search quality for each `efSearch` value; returns a list of result dicts containing: `M`, `ef_construction`, `ef_search`, `build_time_s`, `search_time_ms` (per query), `recall_at_k`, `memory_mb`
- `recommend(target_recall, max_latency_ms, max_memory_mb=None)` — filters benchmark results to those meeting the recall and latency constraints (and memory if specified), then returns the configuration with the lowest memory usage; if no configuration meets all constraints, returns the one closest to the target recall with a warning flag `"constraints_met": False`
- Must validate that `ground_truth` shape matches `(len(queries), k)` and raise `ValueError` if not

### Recall Calculation

- Recall@k is the fraction of true k-nearest neighbors found in the search results
- Must handle the case where `k` from ground truth differs from the search k by using `min(k_groundtruth, k_search)`

### QuantizationAdvisor Class

- Constructor accepts: `vectors` (numpy array), `metric` (same as above)
- `estimate_memory(index_type, params)` — returns estimated memory in MB for the given index type (`"flat"`, `"hnsw"`, `"ivfpq"`) and parameters
  - `"flat"`: n × d × 4 bytes (float32)
  - `"hnsw"`: n × d × 4 + n × M × 2 × 4 bytes (vectors + graph edges)
  - `"ivfpq"`: n × (code_size) + overhead for centroids
- `recommend_quantization(target_memory_mb, target_recall)` — suggests the least aggressive quantization that meets the memory target:
  - If flat fits → `"none"`
  - If HNSW fits → `"none"` (use HNSW with tuned params)
  - If SQ8 fits → `"scalar_int8"` (scalar quantization to 8-bit integers)
  - If PQ fits → `"product_quantization"` with recommended `m` (subvectors) and `nbits`
  - Returns a dict with `"quantization_type"`, `"estimated_memory_mb"`, `"expected_recall_impact"` (percentage recall drop estimate)
- `apply_quantization(base_index, quantization_config)` — wraps the given FAISS index with the recommended quantization and returns the new index

### Benchmark Integrity

- Benchmark results must be deterministic for the same vectors and parameters
- Build time and search time must be measured using `time.perf_counter()`
- Memory estimates must account for both vector storage and index overhead

### Edge Cases

- Vectors with zero dimensions must raise `ValueError`
- A single query vector must work correctly (not fail on shape)
- `m_values` or `ef_search_values` lists containing values < 2 must raise `ValueError` (HNSW requires M ≥ 2)
- If all benchmark configurations exceed the latency target, `recommend` still returns the best available option with `constraints_met: False`

### Expected Functionality

- Given 10,000 128-dimensional vectors, benchmarking M=[16, 32] × efConstruction=[128, 256] × efSearch=[64, 128] returns 8 result dicts with measured performance
- `recommend(target_recall=0.95, max_latency_ms=5)` returns the configuration that achieves ≥ 0.95 recall within 5ms per query at minimum memory
- `estimate_memory("hnsw", {"n": 1_000_000, "d": 128, "M": 32})` returns the correct estimate in MB
- `recommend_quantization(target_memory_mb=100)` for 1M 128-d vectors (raw ~488 MB) should suggest product quantization

## Acceptance Criteria

- FAISS builds successfully with the created module files
- `HNSWTuner.benchmark()` produces correct recall and timing measurements for each parameter combination
- `HNSWTuner.recommend()` returns valid configurations meeting the specified constraints, or the closest match with a warning
- `QuantizationAdvisor.estimate_memory()` returns correct memory estimates for flat, HNSW, and IVFPQ index types
- `QuantizationAdvisor.recommend_quantization()` recommends the least aggressive quantization meeting the memory target
- Invalid inputs raise `ValueError` with descriptive messages
- Tests verify tuning and quantization logic using synthetic datasets
