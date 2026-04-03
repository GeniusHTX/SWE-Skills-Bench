# Task: Implement a Hybrid Similarity Search Service with Multiple Index Types

## Background

A product recommendation service needs a similarity search backend that supports multiple distance metrics, index types, and hybrid (dense + sparse) search. The service must handle a catalog of 1 million product embeddings with metadata filtering, provide configurable index strategies (Flat, HNSW, IVF+PQ), and expose a REST API. The implementation uses Pinecone as the vector database with a local FAISS fallback for development.

## Files to Create/Modify

- `src/similarity/__init__.py` (create) — Package init exporting `SimilarityService`, `PineconeStore`, `FAISSStore`, `HybridSearcher`
- `src/similarity/pinecone_store.py` (create) — `PineconeStore` class wrapping Pinecone client with batch upsert, filtered search, and namespace management
- `src/similarity/faiss_store.py` (create) — `FAISSStore` class wrapping FAISS with Flat, HNSW, and IVF+PQ index construction and search
- `src/similarity/hybrid.py` (create) — `HybridSearcher` combining dense vector search with BM25 sparse search using configurable RRF or weighted fusion
- `src/similarity/reranker.py` (create) — `CrossEncoderReranker` using `cross-encoder/ms-marco-MiniLM-L-6-v2` for result reranking
- `src/similarity/api.py` (create) — FastAPI REST endpoints for search, upsert, index management, and health check
- `src/similarity/models.py` (create) — Pydantic models for API request/response schemas
- `tests/test_faiss_store.py` (create) — Tests for FAISS index creation, search accuracy, and index type comparison
- `tests/test_hybrid.py` (create) — Tests for hybrid search fusion and weighting behavior
- `tests/test_api.py` (create) — API integration tests using TestClient

## Requirements

### Pinecone Store (`src/similarity/pinecone_store.py`)

- `PineconeStore.__init__(api_key: str, index_name: str, dimension: int = 1536, metric: str = "cosine")` — create index if not exists with `ServerlessSpec(cloud="aws", region="us-east-1")`.
- `PineconeStore.upsert(vectors: list[dict], namespace: str = "", batch_size: int = 100) -> int` — batch upsert vectors. Each vector is `{"id": str, "values": list[float], "metadata": dict}`. Returns total upserted count.
- `PineconeStore.search(query_vector: list[float], top_k: int = 10, namespace: str = "", filter: dict | None = None) -> list[SearchResult]` — returns results with `id`, `score`, `metadata`.
- `PineconeStore.delete(ids: list[str], namespace: str = "") -> int` — delete vectors by ID, return count deleted.
- `PineconeStore.describe() -> dict` — return index stats: `{"dimension": int, "total_vectors": int, "namespaces": dict}`.
- Metadata filter support per Pinecone syntax: `{"category": {"$eq": "electronics"}, "price": {"$lte": 100.0}}`.

### FAISS Store (`src/similarity/faiss_store.py`)

- `FAISSStore.__init__(dimension: int, index_type: str = "flat", metric: str = "cosine")`:
  - `"flat"` → `faiss.IndexFlatIP` (after L2-normalizing for cosine) or `faiss.IndexFlatL2` for euclidean.
  - `"hnsw"` → `faiss.IndexHNSWFlat` with `M=32`, `efConstruction=200`, `efSearch=100`.
  - `"ivfpq"` → `faiss.IndexIVFPQ` with `nlist=256`, `m=16` (number of subquantizers), `nbits=8`. Requires training on at least 10,000 vectors.

- `FAISSStore.add(vectors: np.ndarray, ids: list[str]) -> int` — add vectors, maintain ID mapping. Returns count added.
- `FAISSStore.search(query_vector: np.ndarray, top_k: int = 10) -> list[SearchResult]` — search and return results with `id`, `score`.
- `FAISSStore.search_with_filter(query_vector: np.ndarray, top_k: int, filter_fn: Callable[[str], bool]) -> list[SearchResult]` — post-filter results: search for `top_k * 5` candidates, apply `filter_fn` on IDs/metadata, return top `top_k` passing.
- `FAISSStore.train(vectors: np.ndarray)` — required for IVF+PQ index before adding vectors. Raise `ValueError("IVF+PQ index requires training. Call train() with at least 10000 vectors first.")` if attempting to add to untrained IVF+PQ.
- `FAISSStore.save(path: str)` / `FAISSStore.load(path: str)` — serialize/deserialize index and ID mapping.

### Hybrid Searcher (`src/similarity/hybrid.py`)

- `HybridSearcher.__init__(dense_store: PineconeStore | FAISSStore, documents: list[str], fusion: str = "rrf", dense_weight: float = 0.7)`:
  - `fusion="rrf"` — Reciprocal Rank Fusion with `k=60`: `rrf_score = dense_weight * 1/(k+rank_dense) + (1-dense_weight) * 1/(k+rank_sparse)`.
  - `fusion="weighted"` — normalized score fusion: `score = dense_weight * norm_dense_score + (1-dense_weight) * norm_sparse_score`.
- Internal BM25 index built from `documents` list using `rank_bm25.BM25Okapi`.
- `HybridSearcher.search(query: str, query_vector: list[float], top_k: int = 10) -> list[SearchResult]` — run both searches, fuse results.

### Cross-Encoder Reranker (`src/similarity/reranker.py`)

- `CrossEncoderReranker.__init__(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2")`.
- `CrossEncoderReranker.rerank(query: str, results: list[SearchResult], top_k: int = 5) -> list[SearchResult]` — score each (query, result.text) pair, sort by score, return top-k with `rerank_score` field added.

### REST API (`src/similarity/api.py`)

Endpoints:

- `POST /search` — body: `{"query_vector": list[float], "top_k": int, "filter": dict | None, "namespace": str, "rerank": bool, "query_text": str | None}`. Returns `{"results": [{"id": str, "score": float, "metadata": dict}], "search_time_ms": float}`.
- `POST /hybrid-search` — body: `{"query_text": str, "query_vector": list[float], "top_k": int, "fusion": str, "dense_weight": float}`. Returns same format as `/search`.
- `POST /upsert` — body: `{"vectors": [{"id": str, "values": list[float], "metadata": dict}], "namespace": str}`. Returns `{"upserted_count": int}`.
- `DELETE /vectors` — body: `{"ids": list[str], "namespace": str}`. Returns `{"deleted_count": int}`.
- `GET /index/stats` — returns index statistics.
- `GET /health` — returns `{"status": "healthy", "index_type": str, "total_vectors": int}`.

All endpoints return errors as `{"error": str, "detail": str}` with appropriate HTTP status codes (400 for validation, 404 for not found, 500 for internal).

### Expected Functionality

- `POST /upsert` with 500 vectors → returns `{"upserted_count": 500}`.
- `POST /search` with a query vector and `filter: {"category": {"$eq": "electronics"}}` → returns only electronics products, sorted by similarity.
- `POST /hybrid-search` with `query_text="wireless noise cancelling headphones"` and embedding → returns results combining semantic and keyword match.
- FAISSStore with `"hnsw"` index achieves recall@10 ≥ 0.95 compared to flat index on 10,000 test vectors.
- FAISSStore with `"ivfpq"` index raises `ValueError` if `add()` is called before `train()`.
- `GET /health` → `{"status": "healthy", "index_type": "hnsw", "total_vectors": 50000}`.

## Acceptance Criteria

- `PineconeStore` supports batch upsert (100 per batch), filtered search with Pinecone metadata filter syntax, and namespace isolation.
- `FAISSStore` supports three index types (flat, HNSW, IVF+PQ) with correct initialization parameters and training workflow.
- HNSW index uses `M=32`, `efConstruction=200`, `efSearch=100`. IVF+PQ uses `nlist=256`, `m=16`, `nbits=8`.
- IVF+PQ index enforces training before vector addition.
- Hybrid search combines dense and sparse results using either RRF (k=60) or weighted score fusion with configurable dense/sparse weighting.
- Cross-encoder reranker reorders results and adds rerank_score.
- REST API validates request bodies with Pydantic and returns structured error responses with appropriate HTTP status codes.
- FAISS index can be saved to and loaded from disk with consistent search results.
