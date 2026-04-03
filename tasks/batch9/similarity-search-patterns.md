# Task: Implement a Hybrid Search Collection with Weighted Scoring in Milvus

## Background

Milvus (https://github.com/milvus-io/milvus) is a vector database for similarity search. A new Go package is needed that implements a hybrid search collection combining dense vector search (HNSW), sparse vector search (BM25-weighted), and scalar filtering into a unified scoring pipeline. The implementation adds a new collection type to the Milvus internal APIs that supports weighted score fusion across multiple search strategies.

## Files to Create/Modify

- `internal/core/src/segcore/hybrid_search.go` (create) — `HybridSearcher` struct implementing the hybrid search pipeline: execute dense search, sparse search, and scalar filter in parallel, then fuse results using weighted reciprocal rank fusion
- `internal/core/src/segcore/score_fusion.go` (create) — Score fusion algorithms: Reciprocal Rank Fusion (RRF), Convex Combination, and Relative Score Fusion
- `internal/core/src/segcore/hybrid_search_test.go` (create) — Unit tests for score fusion correctness, rank ordering, tie-breaking, and edge cases
- `internal/proxy/hybrid_search_handler.go` (create) — Proxy handler that accepts hybrid search requests with per-strategy weights and dispatches to the searcher
- `configs/hybrid_search.yaml` (create) — Default configuration for hybrid search parameters (weights, RRF k-constant, max candidates per strategy)

## Requirements

### Score Fusion (`score_fusion.go`)

- Function `ReciprocalRankFusion(rankings [][]SearchResult, weights []float64, k int) []FusedResult` where:
  - `SearchResult` contains `ID int64`, `Score float64`, `Rank int`
  - `FusedResult` contains `ID int64`, `FusedScore float64`, `Scores map[string]float64` (per-strategy scores)
  - For each result at rank `r` in strategy `i`: `score += weights[i] * 1.0 / (k + r)` where `k` defaults to 60
  - Results appearing in multiple strategies get summed scores
  - Return results sorted by `FusedScore` descending
- Function `ConvexCombination(rankings [][]SearchResult, weights []float64) []FusedResult`:
  - Normalize each strategy's scores to [0, 1] range using min-max normalization
  - `FusedScore = sum(weights[i] * normalized_score_i)` for each result
  - Weights must sum to 1.0; return error if they don't (tolerance 0.001)
- Function `RelativeScoreFusion(rankings [][]SearchResult, weights []float64) []FusedResult`:
  - Convert each strategy's scores to percentile ranks within that strategy
  - `FusedScore = sum(weights[i] * percentile_rank_i)`
- All functions must handle empty ranking lists gracefully (return empty result)
- Tie-breaking: for equal `FusedScore`, prefer the result with the lower ID

### Hybrid Searcher (`hybrid_search.go`)

- Struct `HybridSearcher` with fields: `denseIndex`, `sparseIndex`, `scalarStore`, `fusionMethod string`, `topK int`
- Method `Search(ctx context.Context, req HybridSearchRequest) ([]FusedResult, error)` where `HybridSearchRequest` contains:
  - `DenseVector []float32` (query embedding)
  - `SparseTokens map[string]float32` (BM25 query terms with weights)
  - `ScalarFilters map[string]interface{}` (field name → filter value)
  - `DenseWeight float64`, `SparseWeight float64` (must sum to 1.0)
  - `FusionMethod string` (one of `"rrf"`, `"convex"`, `"relative"`)
  - `TopK int`
  - `DenseCandidates int` (number of candidates to retrieve from dense search, default 100)
  - `SparseCandidates int` (number of candidates from sparse search, default 100)
- Execution pipeline:
  1. Execute dense vector search and sparse search concurrently using goroutines with `errgroup`
  2. Apply scalar filters to both result sets (remove results not matching filters)
  3. Fuse using the specified fusion method
  4. Return top `TopK` results
- If `DenseVector` is nil, skip dense search (sparse-only mode)
- If `SparseTokens` is nil or empty, skip sparse search (dense-only mode)
- Both nil/empty should return error `"at least one search modality required"`

### Configuration (`hybrid_search.yaml`)

- `fusion.default_method`: `"rrf"`
- `fusion.rrf_k`: `60`
- `fusion.default_dense_weight`: `0.6`
- `fusion.default_sparse_weight`: `0.4`
- `search.default_dense_candidates`: `100`
- `search.default_sparse_candidates`: `100`
- `search.max_top_k`: `10000`
- `search.timeout_ms`: `5000`

### Expected Functionality

- Dense search returning IDs [1,2,3,4,5] and sparse search returning IDs [3,5,6,7,8] with RRF fusion produces a merged ranking where ID 3 and 5 (appearing in both) rank highest
- Convex combination with weights [0.7, 0.3] produces different rankings than RRF for the same inputs
- Scalar filter `{"category": "electronics"}` removes results not matching from both dense and sparse results before fusion
- Sparse-only search (nil dense vector) produces results from sparse search alone without fusion errors

## Acceptance Criteria

- RRF correctly sums reciprocal ranks across strategies with configurable k-constant
- Convex combination validates weight sum = 1.0 and normalizes scores to [0, 1]
- Relative score fusion correctly converts to percentile ranks
- `HybridSearcher.Search` executes dense and sparse searches concurrently using goroutines
- Scalar filters correctly exclude non-matching results from both strategies before fusion
- Edge cases handled: empty results, single-strategy mode, nil vectors
- `make milvus` compiles successfully
- `python -m pytest /workspace/tests/test_similarity_search_patterns.py -v --tb=short` passes
