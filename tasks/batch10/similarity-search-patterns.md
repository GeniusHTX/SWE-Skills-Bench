# Task: Implement Multi-Metric Similarity Search with Reranking in Milvus

## Background

Milvus needs a new query path that supports executing a single search request against multiple distance metrics (cosine, L2, inner product) in parallel, fusing the ranked results, and applying an optional server-side reranking stage. This feature targets hybrid retrieval workflows where clients embed the same query with different models or need to compare metric behaviors without issuing separate RPCs. The implementation lives in the Go codebase under `internal/` and `pkg/`.

## Files to Create/Modify

- `internal/querynodev2/services/multi_metric_search.go` (new) — Core search handler that accepts a list of metric types per request, dispatches parallel single-metric searches on the segment, and fuses results via Reciprocal Rank Fusion (RRF)
- `internal/querynodev2/services/reranker.go` (new) — Server-side reranking module supporting score-based reranking with min-max normalization and weighted linear combination, plus a Maximal Marginal Relevance (MMR) mode for diversity
- `pkg/util/distance/distance_metrics.go` (new) — Pure-function implementations of cosine similarity, L2 distance, inner product, and Manhattan (L1) distance operating on `[]float32` slices, plus a score normalization utility
- `pkg/util/distance/distance_metrics_test.go` (new) — Unit tests for all distance functions and normalization
- `internal/querynodev2/services/multi_metric_search_test.go` (new) — Unit tests for multi-metric search fusion and reranking
- `internal/querynodev2/services/reranker_test.go` (new) — Unit tests for reranker modes

## Requirements

### Distance Metrics (`distance_metrics.go`)

- Implement `CosineSimilarity(a, b []float32) (float32, error)` — return `dot(a,b) / (norm(a) * norm(b))`; return error if slices differ in length or either has zero norm
- Implement `L2Distance(a, b []float32) (float32, error)` — return `sqrt(sum((a_i - b_i)^2))`; return error if slices differ in length
- Implement `InnerProduct(a, b []float32) (float32, error)` — return `sum(a_i * b_i)`; return error if slices differ in length
- Implement `ManhattanDistance(a, b []float32) (float32, error)` — return `sum(|a_i - b_i|)`; return error if slices differ in length
- Implement `NormalizeScores(scores []float32) []float32` — min-max normalize to `[0, 1]`; if all scores are identical return a slice of `0.5` values; handle empty input by returning empty slice
- All functions must not mutate input slices

### Multi-Metric Search (`multi_metric_search.go`)

- Define `MultiMetricSearchRequest` struct with fields: `Vectors [][]float32`, `MetricTypes []string` (one per vector, valid values: `"cosine"`, `"l2"`, `"ip"`), `TopK int`, `RerankMode string` (one of `"rrf"`, `"mmr"`, `"none"`), `RerankParams map[string]float64`
- Define `SearchResult` struct with fields: `ID int64`, `Score float32`, `Metrics map[string]float32` (individual per-metric scores)
- Implement `ExecuteMultiMetricSearch(req MultiMetricSearchRequest, segments []Segment) ([]SearchResult, error)`:
  1. Validate: `len(Vectors)` must equal `len(MetricTypes)`, `TopK > 0`, all metric types are supported; return descriptive error otherwise
  2. For each `(vector, metric)` pair, execute search on segments and collect per-metric result lists
  3. Fuse results: if `RerankMode == "rrf"`, apply RRF with `k` from `RerankParams["k"]` (default 60); if `"none"`, use the first metric's ranking
  4. Return top-K fused results with all per-metric scores populated
- RRF formula: for each document, `rrf_score = Σ_metric (weight_metric / (k + rank_in_metric))`; weights from `RerankParams["weight_<metric>"]`, default `1.0` each

### Reranker (`reranker.go`)

- Implement `RerankByScore(results []SearchResult, weights map[string]float64) []SearchResult` — compute weighted linear combination of normalized per-metric scores, sort descending
- Implement `RerankByMMR(results []SearchResult, queryVector []float32, lambda float64, topK int) ([]SearchResult, error)`:
  - Iteratively select the result that maximizes `lambda * relevance - (1 - lambda) * max_similarity_to_selected`
  - `relevance` is the result's fused score; similarity to selected is cosine similarity between result vectors
  - `lambda` in `[0, 1]`; return error if `lambda < 0` or `lambda > 1`
  - Return exactly `topK` results (or fewer if input is smaller)
- Implement `Deduplicate(results []SearchResult) []SearchResult` — remove entries with duplicate IDs, keeping the one with the highest score

### Expected Functionality

- `CosineSimilarity([]float32{1, 0}, []float32{0, 1})` → `0.0`
- `CosineSimilarity([]float32{1, 0}, []float32{1, 0})` → `1.0`
- `CosineSimilarity([]float32{1, 0}, []float32{1})` → error (length mismatch)
- `CosineSimilarity([]float32{0, 0}, []float32{1, 0})` → error (zero norm)
- `L2Distance([]float32{0, 0}, []float32{3, 4})` → `5.0`
- `NormalizeScores([]float32{2, 5, 8})` → `[]float32{0.0, 0.5, 1.0}`
- `NormalizeScores([]float32{3, 3, 3})` → `[]float32{0.5, 0.5, 0.5}`
- `NormalizeScores([]float32{})` → `[]float32{}`
- Multi-metric search with `MetricTypes=["cosine", "l2"]` and `RerankMode="rrf"` → returns results where a document ranking highly in both metrics has a higher fused score than one ranking highly in only one
- Multi-metric search with `len(Vectors)=2, len(MetricTypes)=1` → returns error about vector/metric count mismatch
- Multi-metric search with `TopK=0` → returns error
- `RerankByMMR` with `lambda=1.0` → ordering is purely by relevance score (no diversity penalty)
- `RerankByMMR` with `lambda=0.0` → each successive pick maximally differs from already-selected results
- `RerankByMMR` with `lambda=1.5` → returns error (out of range)
- `Deduplicate` on results containing `[{ID:1, Score:0.9}, {ID:1, Score:0.7}, {ID:2, Score:0.8}]` → returns `[{ID:1, Score:0.9}, {ID:2, Score:0.8}]`

## Acceptance Criteria

- `make milvus` completes successfully with the new Go files compiled
- `go test ./pkg/util/distance/ -v -run TestDistance` passes all distance metric tests
- `go test ./internal/querynodev2/services/ -v -run TestMultiMetric` passes all multi-metric search tests
- `go test ./internal/querynodev2/services/ -v -run TestReranker` passes all reranker tests
- Distance functions return correct results for orthogonal, identical, and opposite vectors
- RRF fusion produces different rankings than any single metric when metrics disagree
- MMR reranking with `lambda=0.5` returns more diverse results than score-only reranking on a dataset with clustered embeddings
- All error cases (length mismatch, zero norm, invalid parameters) return descriptive errors without panicking
- No new external Go module dependencies are introduced
