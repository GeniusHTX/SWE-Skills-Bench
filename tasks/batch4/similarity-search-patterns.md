# Task: Implement a Similarity Search Engine with Multi-Index Support for Milvus

## Background

The Milvus repository (https://github.com/milvus-io/milvus) is a vector database for scalable similarity search. A new Python SDK utility module is needed that provides a high-level similarity search engine supporting multiple index types (Flat, HNSW, IVF_PQ), automatic index selection based on dataset characteristics, hybrid search combining vector similarity with scalar filtering, and batch search with result aggregation.

## Files to Create/Modify

- `scripts/similarity_engine/engine.py` (create) — `SimilarityEngine` class with multi-index support, hybrid search, and auto-index selection
- `scripts/similarity_engine/index_advisor.py` (create) — `IndexAdvisor` class that recommends index type and parameters based on dataset characteristics
- `scripts/similarity_engine/batch_search.py` (create) — `BatchSearcher` class for parallel multi-query search with result aggregation
- `scripts/similarity_engine/__init__.py` (create) — Package init
- `tests/python/test_similarity_engine.py` (create) — Tests using synthetic vectors

## Requirements

### SimilarityEngine Class

- Constructor accepts: `dimension` (int), `metric_type` (one of `"L2"`, `"IP"`, `"COSINE"`, default `"COSINE"`), `index_type` (str, default `"HNSW"`), `index_params` (dict, optional)
- `insert(vectors: numpy.ndarray, ids: list[int], metadata: list[dict] = None)` — inserts vectors with optional metadata; validates that vectors shape is `(n, dimension)` and raises `ValueError` if not
- `search(query_vector: numpy.ndarray, top_k: int = 10, filter_expr: str = None) -> list[dict]` — returns top-k results as `[{"id": int, "distance": float, "metadata": dict}, ...]` sorted by ascending distance (L2) or descending similarity (IP/COSINE)
- `hybrid_search(query_vector: numpy.ndarray, filter_expr: str, top_k: int = 10) -> list[dict]` — combines vector search with scalar filtering expression (e.g., `"category == 'electronics' and price < 100"`)
- `delete(ids: list[int])` — removes vectors by ID; raises `ValueError` if any ID does not exist
- `count() -> int` — returns the total number of indexed vectors
- Default HNSW params: `{"M": 16, "efConstruction": 256}`; default IVF_PQ params: `{"nlist": 128, "m": 8, "nbits": 8}`

### IndexAdvisor Class

- `recommend(num_vectors: int, dimension: int, query_latency_target_ms: float = None, memory_budget_mb: float = None) -> dict` — returns `{"index_type": str, "index_params": dict, "estimated_memory_mb": float, "estimated_recall": float}`
- Selection logic:
  - < 10,000 vectors: `"FLAT"` (exact search, no parameters needed)
  - 10,000–1,000,000 vectors: `"HNSW"` with M=16, efConstruction=256
  - > 1,000,000 vectors: `"IVF_PQ"` with nlist=sqrt(n), m=dimension//8, nbits=8
- If `memory_budget_mb` is provided and HNSW exceeds it, fall back to `"IVF_PQ"`
- Memory estimates:
  - FLAT: `num_vectors × dimension × 4 / 1024 / 1024` MB
  - HNSW: `num_vectors × (dimension × 4 + M × 2 × 8) / 1024 / 1024` MB
  - IVF_PQ: `num_vectors × m × 1 / 1024 / 1024` MB (approximate)

### BatchSearcher Class

- Constructor accepts: `engine` (SimilarityEngine), `max_concurrent` (int, default 10)
- `search_batch(queries: list[numpy.ndarray], top_k: int = 10) -> list[list[dict]]` — searches for all queries and returns a list of result lists
- `search_and_aggregate(queries: list[numpy.ndarray], top_k: int = 10, aggregation: str = "union") -> list[dict]` — searches all queries and aggregates:
  - `"union"`: returns all unique results across queries, sorted by best score
  - `"intersection"`: returns only results appearing in all query result sets
  - `"rrf"`: Reciprocal Rank Fusion across all query result sets with k=60
- Must handle empty query lists by returning an empty list

### Filter Expression Parsing

- Support basic comparison operators: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Support logical operators: `and`, `or`, `not`
- Support string, integer, and float literal values
- Invalid filter expressions must raise `ValueError` with a message indicating the parse error location

### Expected Functionality

- Inserting 1000 128-d vectors and searching with a random query returns 10 results sorted by distance
- Hybrid search with filter `"category == 'electronics'"` returns only results with matching metadata
- `IndexAdvisor.recommend(500)` returns `{"index_type": "FLAT", ...}`
- `IndexAdvisor.recommend(500_000)` returns `{"index_type": "HNSW", ...}`
- `IndexAdvisor.recommend(5_000_000)` returns `{"index_type": "IVF_PQ", ...}`
- Batch search with 5 queries returns 5 result lists; RRF aggregation returns a single fused ranking

## Acceptance Criteria

- The Milvus project builds successfully with the created module files
- SimilarityEngine correctly indexes and retrieves vectors with the specified metric type
- Hybrid search applies both vector similarity and scalar filter correctly
- IndexAdvisor recommends the correct index type based on dataset size and memory constraints
- BatchSearcher supports union, intersection, and RRF aggregation of multi-query results
- Invalid inputs (wrong dimensions, nonexistent IDs, bad filter expressions) raise `ValueError`
- Tests verify search correctness, index selection, and aggregation using synthetic datasets
