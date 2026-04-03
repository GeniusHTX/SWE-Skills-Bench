# Task: Implement a Filtered Vector Search Operator with Dynamic Pruning in Milvus

## Background

Milvus (https://github.com/milvus-io/milvus) is an open-source vector database designed for similarity search at scale. The task is to implement a filtered vector search operator that combines vector similarity search with attribute-based filtering, using a dynamic pruning strategy that decides at query time whether to apply pre-filtering (filter first, then vector search on filtered subset) or post-filtering (vector search first, then filter results) based on estimated selectivity.

## Files to Create/Modify

- `internal/querynodev2/segments/filtered_search.go` (create) — `FilteredSearchOperator` that performs vector search with attribute filtering and dynamic pruning strategy selection
- `internal/querynodev2/segments/selectivity_estimator.go` (create) — `SelectivityEstimator` that estimates the fraction of vectors matching a boolean filter expression
- `internal/querynodev2/segments/filtered_search_test.go` (create) — Unit tests for the filtered search operator
- `internal/querynodev2/segments/selectivity_estimator_test.go` (create) — Unit tests for selectivity estimation
- `pkg/util/similarity/metrics.go` (modify) — Add a `CosineDistance` function alongside existing metrics

## Requirements

### `SelectivityEstimator` (`selectivity_estimator.go`)

```go
type SelectivityEstimator struct {
    segmentStats map[int64]*SegmentStats  // segment ID -> stats
}

type SegmentStats struct {
    TotalRows     int64
    FieldStats    map[string]*FieldStats
}

type FieldStats struct {
    FieldName    string
    FieldType    string     // "int64", "float64", "varchar", "bool"
    Min          interface{}
    Max          interface{}
    NullCount    int64
    DistinctCount int64
}
```

#### Methods

- `EstimateSelectivity(filter *FilterExpression, segmentID int64) float64`:
  - For equality filters (`field == value`): estimate as `1.0 / distinctCount`
  - For range filters (`field > value`): estimate as `(max - value) / (max - min)` for numeric fields
  - For IN filters (`field IN [values]`): estimate as `len(values) / distinctCount`
  - For AND combinations: multiply individual selectivities (assume independence)
  - For OR combinations: `1 - (1 - sel_A) * (1 - sel_B)`
  - For NOT: `1 - selectivity`
  - Return a value in `[0.0, 1.0]`; default to `0.5` if no statistics are available

### `FilteredSearchOperator` (`filtered_search.go`)

```go
type FilteredSearchOperator struct {
    estimator          *SelectivityEstimator
    preFilterThreshold  float64  // selectivity below this uses pre-filter (default: 0.2)
    postFilterMultiplier int     // overfetch factor for post-filter (default: 3)
}

type SearchRequest struct {
    Vectors      [][]float32
    TopK         int
    MetricType   string    // "L2", "IP", "COSINE"
    Filter       *FilterExpression
    SegmentIDs   []int64
}

type SearchResult struct {
    IDs       []int64
    Distances []float32
    Strategy  string    // "pre_filter" or "post_filter"
}
```

#### `Search(req *SearchRequest) (*SearchResult, error)`

1. Estimate filter selectivity using `SelectivityEstimator`
2. Choose strategy:
   - If `selectivity <= preFilterThreshold` (few rows match): use **pre-filter** strategy
   - If `selectivity > preFilterThreshold` (many rows match): use **post-filter** strategy

3. **Pre-filter strategy**:
   a. Apply the filter expression to identify matching row IDs (bitmap)
   b. Perform vector search only on the matching subset
   c. Return top-K results from the filtered vectors

4. **Post-filter strategy**:
   a. Perform vector search requesting `topK * postFilterMultiplier` results (overfetch)
   b. Apply the filter expression to the results
   c. Return up to `topK` filtered results
   d. If filtered results are fewer than `topK`, log a warning but return what's available

5. If `Filter` is nil, perform a standard unfiltered vector search

#### Error Handling
- Return an error if `MetricType` is not one of `"L2"`, `"IP"`, `"COSINE"`
- Return an error if `TopK <= 0` or `TopK > 16384`
- Return an error if `Vectors` is empty

### `CosineDistance` Function (`metrics.go`)

- Add `CosineDistance(a, b []float32) (float32, error)`:
  - Returns `1.0 - CosineSimilarity(a, b)`
  - Returns an error if vectors have different lengths or zero magnitude
- Ensure it integrates with the existing similarity metric framework (alongside `L2Distance` and `InnerProduct`)

### Filter Expression Types

Define a `FilterExpression` interface supporting these concrete types:
```go
type CompareExpr struct {
    FieldName string
    Op        string      // "==", "!=", ">", ">=", "<", "<="
    Value     interface{}
}

type InExpr struct {
    FieldName string
    Values    []interface{}
}

type AndExpr struct {
    Left  FilterExpression
    Right FilterExpression
}

type OrExpr struct {
    Left  FilterExpression
    Right FilterExpression
}

type NotExpr struct {
    Expr FilterExpression
}
```

## Expected Functionality

- Given 1M vectors with a "category" field having 100 distinct values:
  - A filter `category == "electronics"` has estimated selectivity 0.01, triggering pre-filter strategy
  - A filter `category != "electronics"` has estimated selectivity 0.99, triggering post-filter strategy
- Pre-filter on a highly selective filter returns exact top-K results within the filtered subset
- Post-filter with `postFilterMultiplier=3` fetches 3×K candidates, filters, and returns up to K
- `CosineDistance([1,0], [0,1])` returns 1.0; `CosineDistance([1,0], [1,0])` returns 0.0

## Acceptance Criteria

- `SelectivityEstimator` correctly estimates selectivity for equality, range, IN, AND, OR, and NOT filter expressions
- `FilteredSearchOperator` dynamically selects pre-filter or post-filter strategy based on estimated selectivity
- Pre-filter strategy applies the filter bitmap before vector search
- Post-filter strategy overfetches by the configured multiplier and filters afterwards
- `SearchResult.Strategy` records which strategy was used
- `CosineDistance` returns correct values and errors on dimension mismatch or zero vectors
- All filter expression types are supported and combinable
- Unit tests cover both strategies, all filter types, and edge cases (empty results, all filtered out, nil filter)
