# Task: Create Similarity Search Demonstration for Milvus

## Background
   Add examples demonstrating similarity search behavior in Milvus with
   index building, vector insertion, and query operations.

## Files to Create/Modify
   - examples/similarity_search_demo.py (new)
   - examples/test_vectors.json (test data)
   - benchmarks/similarity_benchmark.py (optional)

## Requirements
   
   Demo Script:
   - Create collection with proper schema
   - Build appropriate index (IVF_FLAT or HNSW)
   - Insert test vectors with known neighbors
   - Execute similarity queries
   
   Test Dataset:
   - Pre-annotated ground truth neighbors
   - Various vector dimensions
   - Edge cases (identical vectors, orthogonal vectors)
   
   Output Requirements:
   - Top-K results for each query
   - Verify known neighbors in results
   - Query latency and parameters logged

4. Validation:
   - Top-K results contain pre-annotated neighbors
   - Query parameters and latency in output
   - JSON/CSV output format

## Acceptance Criteria
   - `python examples/similarity_search_demo.py` exits with code 0
   - Output contains query parameters and latency
   - Known neighbors appear in top-K results
