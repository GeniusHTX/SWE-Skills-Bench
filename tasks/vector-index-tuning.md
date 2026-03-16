# Task: Create Vector Index Tuning Examples for FAISS

## Background

   Add index tuning examples demonstrating the trade-off between recall
   and latency for different FAISS index configurations.

## Files to Create/Modify

- benchs/index_tuning_demo.py (new)
- examples/index_tuning/ (new directory)
- tools/benchmark_index.py (optional)

## Requirements

   Index Types to Demonstrate:

- Flat (brute force baseline)
- IVF (inverted file)
- HNSW (hierarchical navigable small world)
- PQ (product quantization)

   Benchmark Script:

- Multiple parameter configurations
- Measure recall@K for different nprobe/efSearch values
- Measure query latency
- Output results to CSV/JSON

   Parameters to Vary:

- nlist (for IVF)
- nprobe (for IVF)
- M, efConstruction, efSearch (for HNSW)

4. Output Requirements:
   - recall@10 and recall@100 metrics
   - Query latency in milliseconds
   - Memory usage statistics

## Acceptance Criteria

- `python benchs/index_tuning_demo.py` exits with code 0
- Output contains recall and latency metrics
- Clear trade-off demonstration
