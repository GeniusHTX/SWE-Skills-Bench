# Task: Add a Spark Job Optimization Example to Apache Spark

## Background

Apache Spark (https://github.com/apache/spark) is a distributed computing framework. A new example application is needed that demonstrates key Spark job optimization techniques — partitioning strategies, caching, broadcast variables, and shuffle minimization — with measurable performance comparisons.

## Files to Create

- `examples/src/main/python/spark_optimization_demo.py` — Python Spark job demonstrating optimization techniques (repartitioning, caching, broadcast joins)

## Requirements

### Optimization Demonstrations

- Implement a data processing job that operates on a non-trivial dataset (synthetic or generated)
- Show the impact of repartitioning data appropriately for the workload
- Demonstrate caching intermediate results to avoid redundant computation
- Use broadcast variables to optimize large-table joins with small lookup tables
- Show before/after comparisons for at least one optimization technique

### Benchmarking

- Measure and report execution time for optimized vs. unoptimized versions
- Log key Spark metrics (shuffle bytes read/written, task count, stage duration) where feasible

### Build Integration

- The example must compile as part of the Spark project build without breaking existing modules

## Expected Functionality

- Running the example processes the dataset and prints performance comparison results
- Optimized versions show measurable improvement in execution time or resource usage
- The example completes without runtime errors

## Acceptance Criteria

- The example demonstrates at least one realistic Spark workload in both an unoptimized and optimized form.
- The optimized version uses techniques such as repartitioning, caching, broadcast joins, or shuffle reduction intentionally rather than cosmetically.
- The output includes measurable performance or resource-usage comparisons between the baseline and optimized versions.
- The example highlights why the optimization helps instead of only reporting timings.
- The final implementation is understandable as a teaching example for Spark job optimization.
