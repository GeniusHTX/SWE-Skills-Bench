# Task: Add a Similarity Search Demo to Milvus

## Background

Milvus (https://github.com/milvus-io/milvus) is an open-source vector database for similarity search. A new example or integration script is needed that demonstrates building a collection, inserting vectors, and performing nearest-neighbor queries with different distance metrics and search parameters.

## Files to Create

- `examples/similarity_search_demo.py` — Python script demonstrating collection setup, vector insertion, and nearest-neighbor search with different distance metrics

## Requirements

### Collection Setup

- Create a vector collection with a defined schema (vector dimension, field types, index type)
- Insert a set of sample vectors with associated metadata fields

### Search Operations

- Perform nearest-neighbor search using at least two different distance metrics (e.g., L2 and inner product)
- Demonstrate parameterized search with configurable top-k and search radius or threshold
- Show filtered search combining vector similarity with metadata predicates

### Results

- Display search results with distances/scores and associated metadata
- Compare result quality across different distance metrics or index parameters
- Document the expected behavior for each search scenario

### Build

- The project must build successfully after changes

## Expected Functionality

- Inserting vectors and querying returns the expected nearest neighbors
- Different distance metrics produce appropriately different rankings
- Filtered searches correctly combine vector similarity with metadata constraints

## Acceptance Criteria

- The example creates a collection with vector fields and supporting metadata fields before inserting sample data.
- Search queries can be executed with at least two distance metrics and produce understandable ranking differences.
- Search parameters such as top-k and threshold or radius can be adjusted without changing the core example structure.
- Filtered search combines vector similarity with metadata conditions correctly.
- Result output includes both similarity scores and the metadata needed to interpret the matched records.
