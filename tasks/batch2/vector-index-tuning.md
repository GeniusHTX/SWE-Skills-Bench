# Task: Add a Vector Index Tuning Example to FAISS

## Background

FAISS (https://github.com/facebookresearch/faiss) is a library for efficient similarity search. A new example is needed that demonstrates how to tune vector index parameters to explore the trade-off between recall accuracy and query latency across different index configurations.

## Files to Create

- `tutorial/python/index_tuning_benchmark.py` — Index parameter tuning and recall-vs-latency benchmarking script

## Requirements

### Index Configurations

- Build at least two different index types (e.g., flat, IVF, HNSW, or PQ-based) on the same dataset
- For parameterized indices, vary key tuning knobs (e.g., `nprobe` for IVF, `efSearch` for HNSW, number of clusters)

### Benchmarking

- Measure query latency and recall for each configuration
- Use a ground-truth nearest-neighbor result set for recall computation
- Present results showing how increasing the search effort parameter improves recall at the cost of higher latency

### Dataset

- Use a synthetic or small embedded dataset suitable for demonstration (e.g., random vectors with known nearest neighbors)
- Document the dataset dimensions and size

### Output

- Print or export a comparison table showing index type, configuration parameters, recall@k, and average query time

## Expected Functionality

- Running the example produces a clear comparison of recall vs. latency across index configurations
- Higher search effort consistently improves recall
- The example runs to completion without errors

## Acceptance Criteria

- The example benchmarks at least two index strategies or search-effort configurations on the same dataset.
- Reported results include both latency and recall so the trade-off between speed and accuracy is visible.
- Increasing search effort for the configurable index improves recall in a way that is visible in the benchmark output.
- The example explains the dataset shape and the meaning of the tuned parameters.
- The output is organized so users can compare configurations without reading internal code.
