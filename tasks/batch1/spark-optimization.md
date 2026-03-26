# Task: Add Spark Job Example with Performance Benchmarking

## Background
   Add a small Spark job example with baseline measurement and optimization
   suggestions like shuffle and partition tuning.

## Files to Create/Modify
   - examples/spark_optimization_demo.py (new)
   - examples/spark_benchmark.sh (benchmark script)
   - benchmarks/spark_perf/ (optional directory)

## Requirements
   
   Example Job:
   - Simple but representative workload
   - Configurable data size
   - Clear performance characteristics
   
   Optimization Demonstrations:
   - Shuffle optimization (coalesce vs repartition)
   - Partition tuning
   - Broadcast joins for small tables
   - Caching strategies
   
   Benchmark Script:
   - Measure execution time
   - Record memory usage
   - Compare before/after optimization
   - Output results to JSON/CSV

4. Output Requirements:
   - Performance metrics recorded
   - Comparison results documented
   - Clear speedup demonstration

## Acceptance Criteria
   - `python examples/spark_optimization_demo.py` exits with code 0
   - Comparison results output (JSON/CSV)
   - Performance improvement documented
