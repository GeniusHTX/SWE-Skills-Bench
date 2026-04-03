# Task: Implement an HNSW Auto-Tuning Utility for FAISS

## Background

FAISS (https://github.com/facebookresearch/faiss) is a library for efficient similarity search. The Hierarchical Navigable Small World (HNSW) index is widely used for approximate nearest neighbor search, but tuning its parameters (`M`, `efConstruction`, `efSearch`) for a given dataset requires manual experimentation. The task is to implement a C++ auto-tuning utility and Python wrapper that evaluates HNSW parameter combinations on a sample of the data, measures recall and latency, and returns the Pareto-optimal configurations.

## Files to Create/Modify

- `faiss/AutoTuneHNSW.h` (create) — C++ header for the HNSW auto-tuning utility
- `faiss/AutoTuneHNSW.cpp` (create) — C++ implementation of parameter search, evaluation, and Pareto frontier computation
- `faiss/python/extra_wrappers.py` (modify) — Add Python wrapper functions for the auto-tuning utility
- `tests/test_autotune_hnsw.py` (create) — Python unit tests for the auto-tuning utility
- `faiss/CMakeLists.txt` (modify) — Add `AutoTuneHNSW.cpp` to the build sources

## Requirements

### C++ Auto-Tuning Utility (`AutoTuneHNSW.h/cpp`)

#### `HNSWParameterSet` struct
```cpp
struct HNSWParameterSet {
    int M;                    // Number of connections per element (4-64)
    int efConstruction;       // Construction-time search depth (40-800)
    int efSearch;             // Query-time search depth (16-1024)
};
```

#### `HNSWTuningResult` struct
```cpp
struct HNSWTuningResult {
    HNSWParameterSet params;
    double recall_at_1;       // Recall@1 against ground truth
    double recall_at_10;      // Recall@10 against ground truth
    double qps;               // Queries per second
    double index_build_time;  // Time to build index (seconds)
    double memory_usage_mb;   // Approximate memory usage in MB
};
```

#### `HNSWAutoTuner` class
```cpp
class HNSWAutoTuner {
public:
    HNSWAutoTuner(int dimension, MetricType metric = METRIC_L2);

    // Configure parameter search ranges
    void setMRange(std::vector<int> values);                  // Default: {8, 16, 32, 48, 64}
    void setEfConstructionRange(std::vector<int> values);     // Default: {40, 100, 200, 400}
    void setEfSearchRange(std::vector<int> values);           // Default: {16, 32, 64, 128, 256, 512}

    // Run the auto-tuning process
    // train_vectors: the dataset to index (n x d)
    // query_vectors: queries to evaluate (nq x d)
    // ground_truth: correct k-NN indices for each query (nq x k)
    // k: number of nearest neighbors
    std::vector<HNSWTuningResult> tune(
        const float* train_vectors, idx_t n,
        const float* query_vectors, idx_t nq,
        const idx_t* ground_truth, int k,
        int num_threads = 1
    );

    // Get only Pareto-optimal results (recall vs QPS tradeoff)
    std::vector<HNSWTuningResult> paretoFrontier(
        const std::vector<HNSWTuningResult>& results
    ) const;

    // Get the best configuration for a target recall
    HNSWTuningResult bestForRecall(
        const std::vector<HNSWTuningResult>& results,
        double target_recall_at_1
    ) const;

    // Get the best configuration for a target QPS
    HNSWTuningResult bestForQPS(
        const std::vector<HNSWTuningResult>& results,
        double target_qps
    ) const;
};
```

### Tuning Logic

For each combination of `(M, efConstruction)`:
1. Build an `IndexHNSWFlat` with the given `M` and `efConstruction`
2. Add all `train_vectors` to the index
3. Measure build time and memory usage
4. For each `efSearch` value:
   a. Set `hnsw.efSearch` on the index
   b. Run all queries and measure QPS (queries per second)
   c. Compute `recall@1` and `recall@10` against the ground truth
   d. Store the result as an `HNSWTuningResult`

### Pareto Frontier Computation

- A result is Pareto-optimal if no other result has both higher `recall_at_1` AND higher `qps`
- `paretoFrontier` returns results sorted by ascending `recall_at_1`
- If two results have identical recall, keep the one with higher QPS

### Best Configuration Selection

- `bestForRecall(results, target)`: Among all results with `recall_at_1 >= target`, return the one with highest QPS. If no result meets the target, return the result with highest recall.
- `bestForQPS(results, target)`: Among all results with `qps >= target`, return the one with highest `recall_at_1`. If no result meets the target, return the result with highest QPS.

### Python Wrapper (`extra_wrappers.py`)

Add a function:
```python
def auto_tune_hnsw(train_vectors, query_vectors, ground_truth, k=10,
                   M_range=None, ef_construction_range=None, ef_search_range=None,
                   metric="l2", num_threads=1):
```
- Returns a list of dicts with keys: `params` (dict with `M`, `efConstruction`, `efSearch`), `recall_at_1`, `recall_at_10`, `qps`, `index_build_time`, `memory_usage_mb`
- Also add `pareto_frontier(results)` and `best_for_recall(results, target)` Python functions

## Expected Functionality

- Given 10,000 128-dimensional random vectors, 1,000 queries, and brute-force ground truth:
  - `tune()` evaluates all parameter combinations and returns a list of `HNSWTuningResult` entries
  - Higher `M` and `efConstruction` values yield higher recall but lower QPS
  - Higher `efSearch` values yield higher recall but lower QPS for the same index
- `paretoFrontier()` returns a subset of results where no result is dominated on both recall and QPS
- `bestForRecall(results, 0.95)` returns the fastest configuration that achieves ≥95% recall@1

## Acceptance Criteria

- `HNSWAutoTuner::tune` correctly builds HNSW indexes for each `(M, efConstruction)` combination and evaluates all `efSearch` values
- `recall_at_1` and `recall_at_10` are correctly computed against the provided ground truth
- QPS measurements are based on wall-clock time for the query batch
- `paretoFrontier` returns only non-dominated configurations sorted by recall
- `bestForRecall` and `bestForQPS` return the correct configuration per their selection criteria
- Python wrapper functions correctly call the C++ implementation and return Python-native data structures
- The project builds without errors after adding new files to CMakeLists.txt
- Unit tests validate correctness on a small synthetic dataset
