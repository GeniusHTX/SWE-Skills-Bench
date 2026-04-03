# Task: Build a Vector Index Benchmarking and Tuning Framework

## Background

A semantic search platform serving 50 million document embeddings (768 dimensions) needs to optimize its vector index for production. The current HNSW index has 95% recall@10 but 45ms P99 latency, exceeding the 20ms target. Build a benchmarking framework that tests HNSW parameter combinations, evaluates quantization strategies (scalar INT8, product quantization), and recommends optimal configurations for different recall/latency/memory trade-off targets.

## Files to Create/Modify

- `benchmark/index_builder.py` (create) — Build HNSW indexes with different parameter configurations using hnswlib and FAISS
- `benchmark/quantization.py` (create) — Implement and benchmark scalar quantization (INT8) and product quantization (PQ) strategies
- `benchmark/evaluator.py` (create) — Evaluate indexes: measure recall@k, latency (P50/P95/P99), throughput (QPS), and memory usage
- `benchmark/parameter_sweep.py` (create) — Automated parameter sweep across M, efConstruction, efSearch combinations
- `benchmark/recommender.py` (create) — Analyze benchmark results and recommend optimal configuration for given constraints
- `benchmark/report.py` (create) — Generate benchmark report with Pareto frontier plots and configuration comparison tables
- `tests/test_benchmark.py` (create) — Tests for recall calculation, parameter recommendation, and quantization correctness

## Requirements

### Index Builder (`benchmark/index_builder.py`)

Class `HNSWIndexBuilder`:

- `__init__(self, dim: int = 768, metric: str = "cosine")`.
- `build_hnswlib(self, vectors: np.ndarray, M: int = 16, ef_construction: int = 100) -> hnswlib.Index`: Build hnswlib HNSW index. Set `max_elements`, `M`, `ef_construction`. Call `add_items(vectors)`. Return index.
- `build_faiss_hnsw(self, vectors: np.ndarray, M: int = 32, ef_construction: int = 128) -> faiss.IndexHNSWFlat`: Build FAISS HNSW index. Set `hnsw.efConstruction`, add vectors. Return index.
- `build_faiss_ivf(self, vectors: np.ndarray, nlist: int = 1024, nprobe: int = 64) -> faiss.IndexIVFFlat`: Build IVF index with nlist centroids trained on vectors. Return index.
- `save_index(self, index, path: str)` and `load_index(self, path: str, index_type: str)`.

Class `IndexConfig`:
```python
@dataclass
class IndexConfig:
    index_type: str  # "hnsw", "ivf", "hnsw_pq", "ivf_pq"
    M: int = 16
    ef_construction: int = 100
    ef_search: int = 50
    nlist: int = 1024
    nprobe: int = 64
    pq_m: int = 48  # number of PQ sub-quantizers
    pq_bits: int = 8
    scalar_quantization: bool = False
```

### Quantization (`benchmark/quantization.py`)

Class `QuantizationBenchmark`:

- `__init__(self, vectors: np.ndarray, dim: int = 768)`.

**Scalar INT8 Quantization:**
- `quantize_scalar_int8(self) -> tuple[np.ndarray, dict]`: Map float32 vectors to uint8 per-dimension. Compute per-dimension min/max. Store quantization parameters (min, scale). Return quantized vectors and params.
- `dequantize_scalar_int8(self, quantized: np.ndarray, params: dict) -> np.ndarray`: Reconstruct approximate float32 vectors.
- `scalar_quantization_error(self) -> float`: Mean L2 distance between original and reconstructed vectors.

**Product Quantization:**
- `build_pq_index(self, m: int = 48, bits: int = 8) -> faiss.IndexPQ`: Build FAISS PQ index with m sub-quantizers and bits per code.
- `build_opq_index(self, m: int = 48, bits: int = 8) -> faiss.IndexPreTransform`: Build OPQ (Optimized Product Quantization) with rotation matrix.
- `build_hnsw_pq(self, M: int = 32, m_pq: int = 48) -> faiss.IndexHNSWPQ`: Combine HNSW graph with PQ compressed storage.

**Memory Calculations:**
- `estimate_memory(self, n_vectors: int, config: IndexConfig) -> dict`: Return `{"vectors_mb": ..., "graph_mb": ..., "total_mb": ..., "bytes_per_vector": ...}`.
  - FP32: `n × dim × 4` bytes.
  - INT8: `n × dim × 1` bytes + parameters.
  - PQ(m=48, bits=8): `n × m × bits/8` bytes + codebooks.
  - HNSW graph: `n × M × 2 × 4` bytes approximately.

### Evaluator (`benchmark/evaluator.py`)

Class `IndexEvaluator`:

- `__init__(self, ground_truth: np.ndarray)`. Ground truth is precomputed exact kNN results (N_queries × K).
- `recall_at_k(self, predictions: np.ndarray, k: int = 10) -> float`: Fraction of true top-k neighbors found in predicted top-k.
- `precision_at_k(self, predictions: np.ndarray, k: int = 10) -> float`: Same as recall when prediction size equals k.

- `measure_latency(self, index, queries: np.ndarray, k: int = 10, n_runs: int = 100) -> dict`:
  - Warm up with 10 queries.
  - Run n_runs queries sequentially, time each.
  - Return `{"p50_ms": ..., "p95_ms": ..., "p99_ms": ..., "mean_ms": ..., "std_ms": ...}`.

- `measure_throughput(self, index, queries: np.ndarray, k: int = 10, n_threads: int = 4, duration_seconds: int = 10) -> float`:
  - Run queries in parallel for duration_seconds.
  - Return queries per second (QPS).

- `full_evaluation(self, index, queries: np.ndarray, k: int = 10, config: IndexConfig = None) -> dict`:
  - Combine recall, latency, throughput, memory into single report.
  - Return `{"config": ..., "recall@10": ..., "latency": {...}, "throughput_qps": ..., "memory_mb": ..., "index_build_time_s": ...}`.

### Parameter Sweep (`benchmark/parameter_sweep.py`)

Class `ParameterSweep`:

- `__init__(self, vectors: np.ndarray, queries: np.ndarray, ground_truth: np.ndarray)`.
- `hnsw_sweep(self) -> list[dict]`:
  - M values: `[8, 16, 32, 48, 64]`.
  - efConstruction values: `[64, 128, 256, 512]`.
  - efSearch values: `[32, 64, 128, 256, 512]`.
  - For each (M, efConstruction) combination: build index once.
  - For each efSearch: evaluate recall, latency, throughput.
  - Return list of evaluation results.

- `quantization_sweep(self) -> list[dict]`:
  - Test: FP32, INT8 scalar, PQ(m=24), PQ(m=48), PQ(m=96), OPQ(m=48).
  - For each: build index, evaluate recall, latency, memory.

- `save_results(self, results: list[dict], path: str)`: Save as JSON for analysis.

### Recommender (`benchmark/recommender.py`)

Class `ConfigRecommender`:

- `__init__(self, sweep_results: list[dict])`.
- `pareto_frontier(self, x_metric: str = "latency_p99_ms", y_metric: str = "recall@10") -> list[dict]`: Compute Pareto-optimal configurations (no config is better in both metrics).
- `recommend(self, constraints: dict) -> dict`: Given constraints like `{"min_recall": 0.95, "max_latency_p99_ms": 20, "max_memory_gb": 32}`, find the configuration that maximizes recall while meeting all constraints. Return best config and its metrics.
- `recommend_profiles(self) -> dict`: Pre-defined profiles:
  - **"low_latency"**: Minimize P99 latency, recall >= 0.90.
  - **"high_recall"**: Maximize recall >= 0.99, latency < 50ms.
  - **"balanced"**: Recall >= 0.95, latency < 20ms, minimize memory.
  - **"memory_efficient"**: Minimize memory, recall >= 0.90.

### Report (`benchmark/report.py`)

- `generate_report(sweep_results: list[dict], output_dir: str) -> str`:
  - `{output_dir}/benchmark_report.md`: Markdown report with:
    - Summary table: top 10 configs by recall, by latency, by memory efficiency.
    - Pareto frontier chart (matplotlib saved as PNG).
    - Quantization comparison table: FP32 vs INT8 vs PQ recall degradation and memory savings.
    - Recommendation per profile.
  - `{output_dir}/pareto_recall_vs_latency.png`: Scatter plot with Pareto frontier line.
  - `{output_dir}/memory_vs_recall.png`: Memory usage vs recall trade-off chart.

### Unit Tests (`tests/test_benchmark.py`)

- Test `recall_at_k`: predictions `[[1,2,3]]`, ground_truth `[[1,3,5]]` at k=3 → recall = 2/3.
- Test `estimate_memory` FP32: 1M vectors × 768 dim × 4 bytes = 3072 MB.
- Test `estimate_memory` PQ(m=48): 1M vectors × 48 bytes ≈ 48 MB (plus overhead).
- Test `quantize_scalar_int8` roundtrip error < 0.01 mean L2 distance for random vectors.
- Test Pareto frontier: given results with known dominance relationships, verify correct frontier.
- Test recommender with `min_recall=0.95, max_latency_p99_ms=20` returns config meeting both constraints.

### Expected Functionality

- `python -m benchmark.parameter_sweep --vectors data/vectors.npy --queries data/queries.npy --gt data/ground_truth.npy` → runs full sweep, saves results.
- `python -m benchmark.recommender --results results/sweep.json --min-recall 0.95 --max-latency-p99 20 --max-memory-gb 32` → prints recommended config.
- `python -m benchmark.report --results results/sweep.json --output reports/` → generates Markdown report with charts.

## Acceptance Criteria

- Index builder supports hnswlib HNSW, FAISS HNSW, FAISS IVF, and HNSW+PQ composite indexes.
- Quantization module implements scalar INT8 (per-dimension min/max scaling) and product quantization (FAISS PQ and OPQ).
- Memory estimation formulas correctly account for vector storage, graph overhead, and quantization codebooks.
- Evaluator measures recall@k, latency percentiles (P50/P95/P99), and throughput (QPS) with proper warmup.
- Parameter sweep tests M ∈ {8,16,32,48,64}, efConstruction ∈ {64,128,256,512}, efSearch ∈ {32,64,128,256,512}.
- Pareto frontier identifies configurations where no other config dominates in both recall and latency.
- Recommender returns optimal configuration satisfying user-defined constraints on recall, latency, and memory.
- Pre-defined profiles (low_latency, high_recall, balanced, memory_efficient) provide ready-made recommendations.
- Report generates Markdown with comparison tables and PNG scatter plots of Pareto frontiers.
- Unit tests verify recall calculation, memory estimation, quantization roundtrip error, and Pareto frontier correctness.
