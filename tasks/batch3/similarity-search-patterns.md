# Task: Implement Hybrid Search with HNSW and IVF Index Strategies for Milvus

## Background

Milvus (https://github.com/milvus-io/milvus) is an open-source vector database for similarity search. The project needs enhanced search capabilities in the `internal/` package, specifically: a hybrid search engine combining dense vector search with sparse BM25 scoring, configurable index selection between HNSW and IVF, and a reranking module that fuses results from multiple search strategies.

## Files to Create/Modify

- `internal/search/hybrid_searcher.go` (create) — Hybrid search engine combining dense vector and sparse keyword search
- `internal/search/index_selector.go` (create) — Index strategy selector based on dataset characteristics
- `internal/search/reranker.go` (create) — Result reranking with Reciprocal Rank Fusion and score normalization
- `internal/search/hybrid_searcher_test.go` (create) — Tests for hybrid search
- `internal/search/reranker_test.go` (create) — Tests for reranking

## Requirements

### Hybrid Search Engine

- Implement a `HybridSearcher` struct that accepts a `DenseSearcher` interface and a `SparseSearcher` interface
- `DenseSearcher.Search(ctx, vector []float32, topK int) ([]SearchResult, error)` — returns results with `ID`, `Score` (similarity), `Distance`
- `SparseSearcher.Search(ctx, query string, topK int) ([]SearchResult, error)` — returns results with BM25-based scores
- `HybridSearcher.Search(ctx, vector, query, topK, alpha float32)` merges results where `alpha` controls the weight: `final_score = alpha * dense_score + (1 - alpha) * sparse_score`
- `alpha` must be 0.0–1.0; return error if out of range
- Deduplicate results by ID; if the same ID appears in both searchers, its scores are combined

### Index Strategy Selector

- Implement an `IndexSelector` that recommends an index type based on dataset characteristics:
  - **HNSW** (Hierarchical Navigable Small World): recommended when dataset size < 10M vectors, recall requirement > 0.95, and latency requirement < 10ms
  - **IVF_FLAT**: recommended when dataset size >= 10M vectors, recall requirement 0.90–0.95, and memory is not constrained
  - **IVF_PQ** (Product Quantization): recommended when dataset size >= 10M vectors and memory is constrained (> 1B vectors or < 64GB available RAM)
  - **FLAT**: recommended for datasets < 100K vectors (brute-force exact search)
- Input: `DatasetProfile` struct with fields: `num_vectors` (int64), `dimension` (int), `recall_target` (float, 0.0–1.0), `latency_target_ms` (int), `available_memory_gb` (int)
- Output: `IndexRecommendation` with `index_type`, `parameters` (map of recommended params like `M`, `efConstruction` for HNSW, or `nlist`, `nprobe` for IVF), `estimated_memory_gb`, `reasoning` (string explaining the choice)
- HNSW default parameters: `M=16`, `efConstruction=200`; for higher recall targets (> 0.99), increase to `M=32`, `efConstruction=400`
- IVF default parameters: `nlist = sqrt(num_vectors)`, `nprobe = nlist / 10` (minimum 1)

### Reranker

- Implement Reciprocal Rank Fusion (RRF): `score = Σ 1/(k + rank)` where k defaults to 60
- Implement score normalization: min-max normalize scores from each searcher to [0, 1] before combining
- Support a `Reranker` interface with method `Rerank(results [][]SearchResult) []SearchResult`
- The RRF reranker is one implementation; provide a `WeightedScoreReranker` as a second (simply weighted sum of normalized scores)
- Both implementations must handle the case where one searcher returns no results (the other searcher's results are used with solo scores)

### Expected Functionality

- Hybrid search with dense results [A:0.9, B:0.8] and sparse results [B:0.95, C:0.7] and alpha=0.5 produces: B with score (0.5×0.8 + 0.5×0.95), A with 0.5×0.9, C with 0.5×0.7
- Index selector for 5M vectors, 128-dim, recall > 0.95, latency < 10ms recommends HNSW with M=16, efConstruction=200
- Index selector for 100M vectors, 768-dim, recall > 0.90, 32GB RAM recommends IVF_PQ
- RRF with k=60 for results ranked [A, B, C] from searcher 1 and [B, A, D] from searcher 2: B gets highest combined score (rank 2 + rank 1)
- Hybrid search with alpha=1.5 returns error (out of range)

## Acceptance Criteria

- `HybridSearcher` correctly merges dense and sparse results using the alpha weight parameter
- Duplicate IDs across searchers are deduplicated with combined scores
- `IndexSelector` recommends the correct index type based on dataset characteristics with appropriate parameters
- HNSW parameters scale up for recall targets > 0.99
- IVF nlist and nprobe are computed correctly from dataset size
- RRF reranker computes scores correctly with configurable k parameter
- Score normalization maps each searcher's scores to [0, 1] before combination
- Missing results from one searcher are handled gracefully
- Tests cover all index recommendation scenarios, hybrid search combinations, deduplication, and reranking edge cases
