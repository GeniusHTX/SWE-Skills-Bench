# Task: Implement a Collection-Based Similarity Search Service for Milvus

## Background

Milvus (https://github.com/milvus-io/milvus) is an open-source vector database for similarity search. This task requires implementing a Go-based similarity search service that manages collections, handles multi-index strategies (IVF_FLAT and HNSW), supports filtered search with scalar predicates, and provides a batch search API. The service should be implemented as a new internal package.

## Files to Create/Modify

- `internal/search/service.go` (create) — `SearchService` struct managing collection creation, index building, vector insertion, and similarity search operations via the Milvus Go SDK.
- `internal/search/config.go` (create) — Configuration types: `CollectionConfig` (name, dimension, metric type, index type, index params), `SearchConfig` (top_k, nprobe/ef, output fields, filter expression).
- `internal/search/batch.go` (create) — Batch search handler: accepts multiple queries in a single call, executes them concurrently with bounded parallelism, and returns aggregated results.
- `internal/search/filter.go` (create) — Filter expression builder: provides a Go API for constructing Milvus boolean expressions (e.g., `category == "electronics" AND price < 100.0`) from typed parameters, preventing expression injection.
- `internal/search/service_test.go` (create) — Tests for config validation, filter expression building, batch result aggregation, and service method signatures.

## Requirements

### SearchService

- `NewSearchService(address string, options ...Option) (*SearchService, error)` — connects to Milvus instance.
- `CreateCollection(ctx, config CollectionConfig) error` — creates a collection with the specified schema: a primary key `id` (int64, auto-ID), a vector field `embedding` (float vector of given dimension), and optional scalar fields defined in config.
- `BuildIndex(ctx, collectionName string, indexConfig IndexConfig) error` — creates a vector index. Support `IVF_FLAT` (params: nlist) and `HNSW` (params: M, efConstruction).
- `Insert(ctx, collectionName string, embeddings [][]float32, metadata []map[string]interface{}) ([]int64, error)` — insert vectors with metadata, return generated IDs.
- `Search(ctx, collectionName string, query []float32, config SearchConfig) ([]SearchResult, error)` — search with optional filter. `SearchResult` contains `ID`, `Score`, and `Fields` map.
- `Close() error` — graceful disconnect.

### Filter Expression Builder

- `NewFilter()` returns a `FilterBuilder`.
- `Equal(field, value)`, `NotEqual(field, value)`, `GreaterThan(field, value)`, `LessThan(field, value)`, `In(field, values)` — typed builder methods.
- `And(filters ...Filter)`, `Or(filters ...Filter)` — combinators.
- `Build() string` — produces a Milvus boolean expression string. Values are properly quoted (strings get double quotes, numbers are unquoted).
- Builder prevents expression injection by validating field names (alphanumeric + underscore only) and escaping string values.

### Batch Search

- `BatchSearch(ctx, collectionName string, queries [][]float32, config SearchConfig, maxConcurrency int) ([][]SearchResult, error)`.
- Executes queries concurrently using a semaphore of size `maxConcurrency`.
- If any individual query fails, the batch returns partial results with an `errors` field indicating which queries failed.
- Results are returned in the same order as input queries.

### Expected Functionality

- `CreateCollection` with dimension=768, metric=L2, index=HNSW(M=16, efConstruction=200) → collection ready for insert.
- `Insert` 10,000 vectors with `category` and `price` scalar fields → returns 10,000 IDs.
- `Search` with filter `category == "electronics" AND price < 50.0`, top_k=10 → returns up to 10 results matching the filter, sorted by similarity.
- `BatchSearch` with 100 queries and maxConcurrency=10 → returns 100 result sets in order, completed faster than sequential execution.
- `NewFilter().Equal("category", "electronics").LessThan("price", 50.0).Build()` → `category == "electronics" AND price < 50.0`.

## Acceptance Criteria

- `SearchService` implements all CRUD operations with proper context handling and error propagation.
- `FilterBuilder` produces syntactically valid Milvus boolean expressions and prevents injection.
- `BatchSearch` executes concurrently with bounded parallelism and preserves result ordering.
- Config types validate required fields (dimension > 0, metric type in allowed set, top_k > 0).
- Tests verify filter expression generation, config validation, batch result ordering, and error handling.
- Code compiles with `go build ./internal/search/...`.
