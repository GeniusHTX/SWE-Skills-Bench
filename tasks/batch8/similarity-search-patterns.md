# Task: Build a Multi-Backend Similarity Search Service for Milvus

## Background

Milvus (https://github.com/milvus-io/milvus) is a high-performance vector database for similarity search. The project needs a Python client-side similarity search service layer that abstracts over different index types and distance metrics, supports filtered search with metadata predicates, implements batch search with result deduplication, and provides a benchmarking harness to compare index configurations. This service sits on top of Milvus's Python SDK (pymilvus) and adds search pattern implementations commonly needed in production.

## Files to Create/Modify

- `tests/python_client/search_service.py` (create) — `SimilaritySearchService` class managing collections, supporting search with filters, batch search with deduplication, and multi-vector query fusion
- `tests/python_client/index_config.py` (create) — `IndexConfig` dataclass and `IndexFactory` class that creates Milvus index parameter dicts for FLAT, IVF_FLAT, IVF_PQ, and HNSW index types with validated parameters
- `tests/python_client/search_benchmark.py` (create) — `SearchBenchmark` class that runs latency, throughput, and recall benchmarks across multiple index configurations and produces comparison tables
- `tests/python_client/reranker.py` (create) — `SearchReranker` class implementing Maximal Marginal Relevance (MMR) reranking and Reciprocal Rank Fusion (RRF) for combining results from multiple search strategies
- `tests/test_similarity_search_patterns.py` (create) — Tests for index configuration validation, search service methods, reranking algorithms, and benchmark result computation

## Requirements

### IndexConfig and IndexFactory

- `IndexConfig` dataclass fields: `index_type` (str), `metric_type` (str), `params` (dict)
- `IndexFactory.create(index_type: str, metric_type: str = "COSINE", **kwargs) -> IndexConfig`:
  - `"FLAT"`: No additional params required; `metric_type` must be one of `"L2"`, `"IP"`, `"COSINE"`
  - `"IVF_FLAT"`: Required `nlist` (int, 1-65536); optional `nprobe` (int, default 10, must be ≤ nlist)
  - `"IVF_PQ"`: Required `nlist`, `m` (int, number of subquantizers, must divide dimensions evenly), `nbits` (int, 1-16, default 8)
  - `"HNSW"`: Required `M` (int, 4-64), `efConstruction` (int, 8-512); optional `ef` (int, search param, default 64)
- Raise `ValueError` for invalid `index_type`, out-of-range parameters, or invalid `metric_type`
- `to_milvus_params() -> dict` — Convert to the dict format expected by pymilvus `Collection.create_index()`

### SimilaritySearchService

- Constructor: `SimilaritySearchService(collection_name: str, dimension: int, index_config: IndexConfig)`
- `insert(vectors: list[list[float]], metadata: list[dict], ids: list[int] = None) -> list[int]` — Insert vectors with metadata; if `ids` is None, auto-generate sequential IDs starting from 0; validate all vectors have the correct dimension; return the list of inserted IDs
- `search(query_vector: list[float], top_k: int = 10, filters: dict = None) -> list[dict]`:
  - Perform similarity search returning `[{"id": int, "score": float, "metadata": dict}]`
  - `filters` is a dict of metadata field predicates: `{"category": "electronics", "price_lt": 100.0}` — the service translates this into a boolean expression string: field equality uses `==`, `_lt`/`_gt`/`_lte`/`_gte` suffixes map to `<`/`>`/`<=`/`>=`
  - If `filters` is None, no filtering is applied
  - Results sorted by score (lowest distance for L2, highest similarity for COSINE/IP)
- `batch_search(query_vectors: list[list[float]], top_k: int = 10, filters: dict = None) -> list[list[dict]]` — Search for multiple queries at once; return a list of result lists
- `deduplicated_batch_search(query_vectors: list[list[float]], top_k: int = 10) -> list[dict]` — Run batch search, merge all results, remove duplicates by ID (keeping the best score), return the top_k unique results overall
- `multi_vector_search(query_vectors: list[list[float]], weights: list[float], top_k: int = 10) -> list[dict]` — Search with each vector independently, fuse results using weighted score combination: `final_score = Σ(weight_i × score_i)` for each document appearing in any result set; normalize weights to sum to 1.0

### SearchReranker

- `mmr_rerank(results: list[dict], query_embedding: list[float], embeddings: dict[int, list[float]], lambda_param: float = 0.5, top_k: int = 10) -> list[dict]`:
  - Iteratively select results balancing relevance to query (cosine similarity) and diversity from already-selected results
  - `lambda_param=1.0` is pure relevance, `lambda_param=0.0` is pure diversity
  - `embeddings` maps result IDs to their vector embeddings
- `rrf_fuse(result_lists: list[list[dict]], k: int = 60, top_n: int = 10) -> list[dict]`:
  - Reciprocal Rank Fusion: for each document across all result lists, `score = Σ(1 / (k + rank_i))` where `rank_i` is its rank in result list i (1-indexed), or not counted if absent
  - Return top_n by fused score sorted descending
- Cosine similarity computed as `dot(a, b) / (norm(a) * norm(b))`; if either norm is 0, return 0.0

### SearchBenchmark

- Constructor: `SearchBenchmark(dimension: int, n_vectors: int, n_queries: int)`
- `prepare_data(seed: int = 42)` — Generate random float32 database and query vectors; compute brute-force ground truth top-100
- `benchmark_config(index_config: IndexConfig, top_k: int = 10) -> dict`:
  - Insert all vectors, run all queries, return:
    - `recall_at_k`: float
    - `avg_latency_ms`: float
    - `p99_latency_ms`: float (99th percentile)
    - `qps`: float
    - `build_time_s`: float
  - `recall_at_k` = average proportion of true top-k found in predicted top-k
- `compare_configs(configs: list[IndexConfig], top_k: int = 10) -> list[dict]` — Benchmark all configs and return sorted by recall descending
- `find_optimal(target_recall: float = 0.95, configs: list[IndexConfig] = None) -> dict` — Return the config with lowest latency meeting the recall target

### Edge Cases

- Query vector with wrong dimension: raise `ValueError("Expected dimension {d}, got {len(v)}")`
- `top_k` exceeding total inserted vectors: return all available results
- Empty metadata filter: equivalent to no filter
- `multi_vector_search` with weights that don't sum to 1.0: normalize them automatically
- `rrf_fuse` with empty result lists: return empty list
- `mmr_rerank` with `top_k` exceeding input results: return all results

## Expected Functionality

- `IndexFactory.create("HNSW", M=32, efConstruction=200)` returns valid HNSW config with proper parameter ranges
- Inserting 10,000 128-dimensional vectors and searching with a filter `{"category": "electronics"}` returns only matching items
- `deduplicated_batch_search` with 5 queries returns unique results pooled from all queries
- `rrf_fuse` with 3 result lists ranks documents appearing in all lists higher than single-list documents
- `SearchBenchmark.compare_configs()` shows HNSW with M=32 achieving higher recall but higher latency than IVF_FLAT with nlist=128

## Acceptance Criteria

- `IndexFactory` creates valid index configurations and rejects invalid parameters with descriptive errors
- `SimilaritySearchService.search()` supports metadata filtering with equality and comparison operators
- `deduplicated_batch_search` removes ID duplicates and keeps the best score per document
- `multi_vector_search` fuses multi-vector results with weighted scoring and normalized weights
- `SearchReranker` implements MMR and RRF correctly with proper diversity/relevance trade-offs
- `SearchBenchmark` measures recall, latency, and throughput for index comparison
- All tests pass with `pytest`
