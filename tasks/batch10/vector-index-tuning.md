# Task: Implement HNSW Benchmark Suite and Quantization Pipeline for FAISS

## Background

FAISS (https://github.com/facebookresearch/faiss) is Facebook AI's library for efficient similarity search of dense vectors. The project needs a Python-based benchmarking and tuning module that systematically evaluates HNSW index configurations, implements scalar and product quantization pipelines, estimates memory usage across configurations, and provides automated parameter recommendations. This tooling will help operators find the optimal recall/latency/memory trade-off for their vector search workloads.

## Files to Create/Modify

- `faiss/python/hnsw_benchmark.py` (new) — HNSW parameter sweep benchmark: build indexes with different M, efConstruction, efSearch combinations, measure recall@k, search latency (p50/p95/p99), build time, and memory usage
- `faiss/python/quantization.py` (new) — Quantization pipeline: INT8 scalar quantization with configurable min/max clipping, product quantization with KMeans codebook training, binary quantization, and dequantization with error measurement
- `faiss/python/memory_estimator.py` (new) — Memory usage estimator for different index type + quantization combinations, returning vector storage, index overhead, and total memory in MB/GB
- `faiss/python/param_recommender.py` (new) — Parameter recommendation engine that suggests M, efConstruction, efSearch based on dataset size, target recall, max latency, and available memory
- `faiss/python/tests/test_vector_index_tuning.py` (new) — Unit tests for all modules covering numerical correctness, edge cases, and recommendation logic

## Requirements

### HNSW Benchmark (`hnsw_benchmark.py`)

- Implement a `HNSWBenchmark` class accepting `vectors: np.ndarray` (shape `(n, dim)`), `queries: np.ndarray` (shape `(q, dim)`), and `ground_truth: np.ndarray` (shape `(q, k)` — indices of true nearest neighbors)
- Method `run(m_values: list[int], ef_construction_values: list[int], ef_search_values: list[int], k: int = 10) -> list[dict]` must build a FAISS HNSW index for each `(M, efConstruction)` pair, then search with each `efSearch` value, recording:
  - `M`, `ef_construction`, `ef_search`
  - `build_time_s: float`
  - `recall_at_k: float` — fraction of true top-k neighbors found
  - `latency_per_query_ms: float` — average per-query search time
  - `memory_mb: float` — estimated memory of vector storage + graph edges
- Method `find_pareto_optimal(results: list[dict], recall_threshold: float = 0.95) -> list[dict]` must filter to configurations meeting `recall_threshold`, then return only Pareto-optimal configurations (no other config has both higher recall and lower latency)
- Recall calculation: for each query, `|predicted_top_k ∩ true_top_k| / k`, averaged over all queries

### Quantization Pipeline (`quantization.py`)

- Implement `ScalarQuantizerINT8` class:
  - Method `fit(vectors: np.ndarray) -> None` — compute and store `min_val` and `max_val` (or accept explicit values)
  - Method `quantize(vectors: np.ndarray) -> np.ndarray` — scale to 0–255 range and return `uint8` array
  - Method `dequantize(quantized: np.ndarray) -> np.ndarray` — reconstruct `float32` approximation
  - Method `quantization_error(original: np.ndarray) -> float` — mean L2 distance between original and dequantized vectors
- Implement `ProductQuantizer` class:
  - Constructor parameters: `n_subvectors: int` (default `8`), `n_centroids: int` (default `256`)
  - Method `fit(vectors: np.ndarray) -> None` — split vectors into subvectors, train KMeans on each subspace, store codebooks
  - Method `encode(vectors: np.ndarray) -> np.ndarray` — return `uint8` codes of shape `(n, n_subvectors)`
  - Method `decode(codes: np.ndarray) -> np.ndarray` — reconstruct vectors from codes using codebooks
  - Method `compression_ratio(original_dim: int) -> float` — `(original_dim * 4) / (n_subvectors * 1)` (FP32 bytes vs code bytes)
  - Raise `ValueError` if `original_dim % n_subvectors != 0`
- Implement `BinaryQuantizer` class:
  - Method `quantize(vectors: np.ndarray) -> np.ndarray` — convert to binary (positive → 1, else → 0), pack into `uint8` bytes
  - Method `hamming_distance(a: np.ndarray, b: np.ndarray) -> int` — compute Hamming distance between two binary-quantized vectors

### Memory Estimator (`memory_estimator.py`)

- Implement function `estimate_memory(num_vectors: int, dimensions: int, quantization: str, index_type: str = "hnsw", hnsw_m: int = 16) -> dict` returning:
  - `vector_storage_mb: float`
  - `index_overhead_mb: float`
  - `total_mb: float`
  - `total_gb: float`
- Supported `quantization` values: `"fp32"` (4 bytes/dim), `"fp16"` (2), `"int8"` (1), `"pq"` (0.05 approx), `"binary"` (0.125)
- Supported `index_type` values: `"flat"` (no overhead), `"hnsw"` (each node has `M*2` edges at 4 bytes each), `"ivf"` (inverted list pointers + 65536 centroids)
- Raise `ValueError` for unsupported quantization or index_type values

### Parameter Recommender (`param_recommender.py`)

- Implement function `recommend_hnsw_params(num_vectors: int, target_recall: float = 0.95, max_latency_ms: float = 10.0, available_memory_gb: float = 8.0, dimensions: int = 768) -> dict` returning `M`, `ef_construction`, `ef_search`, and a `notes` string
- Logic:
  - For `num_vectors < 100_000`: M=16, efConstruction=100
  - For `100_000 ≤ num_vectors < 1_000_000`: M=32, efConstruction=200
  - For `num_vectors ≥ 1_000_000`: M=48, efConstruction=256
  - efSearch: 256 for recall ≥ 0.99, 128 for recall ≥ 0.95, 64 otherwise
- If estimated memory exceeds `available_memory_gb`, include a `"warning"` key recommending quantization
- Implement function `recommend_quantization(num_vectors: int, dimensions: int, available_memory_gb: float) -> str` returning one of `"fp32"`, `"fp16"`, `"int8"`, `"pq"` based on whether FP32 fits in memory, then FP16, then INT8, otherwise PQ

### Expected Functionality

- `HNSWBenchmark.run(m_values=[16, 32], ef_construction_values=[128], ef_search_values=[64, 128])` on 10K 128-dim random vectors → returns 4 result dicts (2 M × 1 efConstruction × 2 efSearch); each has all required keys
- `find_pareto_optimal` with results `[{recall: 0.90, latency: 5}, {recall: 0.96, latency: 10}, {recall: 0.97, latency: 8}]` and threshold 0.95 → filters out first, returns `{recall: 0.97, latency: 8}` as the only Pareto-optimal point
- `ScalarQuantizerINT8` fit on vectors in range [-1, 1], quantize, dequantize → `quantization_error < 0.01` for 128-dim vectors
- `ProductQuantizer(n_subvectors=8)` on 128-dim vectors → `encode` returns shape `(n, 8)` dtype `uint8`; `compression_ratio(128)` returns `64.0`
- `ProductQuantizer(n_subvectors=7)` on 128-dim vectors → raises `ValueError` (128 not divisible by 7)
- `BinaryQuantizer.hamming_distance` between identical vectors → `0`; between opposite vectors → equals number of packed bytes × 8
- `estimate_memory(1_000_000, 768, "fp32", "hnsw", 16)` → `total_gb > 0` and `vector_storage_mb > index_overhead_mb`
- `estimate_memory(1000, 128, "invalid_type")` → raises `ValueError`
- `recommend_hnsw_params(50_000)` → `M=16, ef_construction=100, ef_search=128`
- `recommend_hnsw_params(5_000_000, available_memory_gb=2.0, dimensions=768)` → result includes `"warning"` key about memory
- `recommend_quantization(10_000_000, 768, 8.0)` where FP32 needs ~29GB → returns `"int8"` (FP16 ~14.5GB still too large, INT8 ~7.3GB fits)

## Acceptance Criteria

- HNSW benchmark correctly builds FAISS indexes with varying parameters and reports recall, latency, and memory for each configuration
- Pareto-optimal filtering retains only non-dominated configurations above the recall threshold
- INT8 scalar quantization round-trips with quantization error below 0.01 for normalized vectors
- Product quantization correctly splits dimensions, trains codebooks, and encodes/decodes vectors
- Binary quantization packs bits into bytes and correctly computes Hamming distance
- Memory estimator returns accurate byte-level calculations for all supported quantization/index combinations
- Parameter recommender adjusts M, efConstruction, and efSearch based on dataset size and recall target
- Memory warnings are emitted when estimated usage exceeds available memory
- The C++ FAISS project builds successfully via `cmake --build build`
- All tests in `faiss/python/tests/test_vector_index_tuning.py` pass via `python -m pytest faiss/python/tests/test_vector_index_tuning.py -v`
