# Task: Add Skew-Resistant Join Optimization to Apache Spark SQL

## Background

Apache Spark (https://github.com/apache/spark) supports Adaptive Query Execution (AQE) for runtime optimization. A new custom Spark SQL optimization rule is needed that detects data skew in sort-merge joins at planning time using column statistics, and automatically rewrites the join to use a salted key strategy when skew is detected. This must be implemented as a Catalyst optimizer rule with unit tests.

## Files to Create/Modify

- `sql/catalyst/src/main/scala/org/apache/spark/sql/catalyst/optimizer/SkewJoinOptimizer.scala` (create) — Catalyst optimizer rule that detects skew in join keys using column statistics and rewrites the logical plan to salt the skewed key
- `sql/catalyst/src/main/scala/org/apache/spark/sql/catalyst/optimizer/SkewDetector.scala` (create) — Utility class that analyzes column statistics (min, max, distinct count, null count, histogram) to detect data skew using a configurable skew threshold
- `sql/core/src/main/scala/org/apache/spark/sql/execution/joins/SkewedSortMergeJoinExec.scala` (create) — Physical execution plan for the skewed join that implements key salting, replicated broadcast of the smaller side's skewed partitions, and union of results
- `sql/catalyst/src/test/scala/org/apache/spark/sql/catalyst/optimizer/SkewJoinOptimizerSuite.scala` (create) — Unit tests for the optimizer rule: detection of skew, plan rewriting, and no-op for non-skewed joins
- `sql/core/src/test/scala/org/apache/spark/sql/execution/joins/SkewedSortMergeJoinSuite.scala` (create) — Integration tests running actual skewed data through the optimized join

## Requirements

### Skew Detection (`SkewDetector.scala`)

- Class `SkewDetector` with method `detectSkew(stats: ColumnStat, threshold: Double = 5.0): Boolean`
- Skew is detected when: the ratio of the most frequent value's count to the average frequency exceeds `threshold`
- If histogram is available: check if any bucket has count exceeding `threshold * (total_rows / num_buckets)`
- If only basic stats are available: check if `(total_rows - null_count) / distinct_count` exceeds threshold (indicates low cardinality with potential skew)
- Method `identifySkewedKeys(stats: ColumnStat, data: Option[DataFrame] = None, topK: Int = 10): Seq[Any]` — Returns the top-K most frequent key values if data sample is available
- Must handle null statistics gracefully (return `false` / empty seq)

### Optimizer Rule (`SkewJoinOptimizer.scala`)

- Extends `Rule[LogicalPlan]` in Catalyst's optimizer framework
- Pattern matches on `Join` nodes with `SortMergeJoin` hint or when join type is `Inner` / `LeftOuter`
- For each join key column, calls `SkewDetector.detectSkew()` using the column's `ColumnStat` from the plan's statistics
- If skew is detected, rewrites the plan:
  1. Add a `salt` column to the skewed side: `withColumn("_salt", rand() * N)` where N is the salt bucket count (configurable, default 10)
  2. Replicate the other side's matching rows N times with explicit salt values 0..N-1
  3. Join on `(original_key, _salt)` instead of just `original_key`
  4. Drop the `_salt` column from the final output
- If skew is not detected, return the plan unchanged
- The rule must be registered in `Optimizer.defaultBatches` under the "Skew Join Optimization" batch

### Physical Execution (`SkewedSortMergeJoinExec.scala`)

- Extends `SparkPlan` with `BinaryExecNode` trait
- `left` and `right` children correspond to the salted and replicated sides
- `doExecute()` implements partitioned sort-merge join on the composite key `(original_key, salt)`
- Metrics: `numOutputRows`, `numSkewedPartitions`, `saltBuckets`
- Must correctly handle null join keys (nulls should not be salted; handle as standard join)

### Configuration

- `spark.sql.optimizer.skewJoin.enabled` (boolean, default `true`) — Master switch for the optimization
- `spark.sql.optimizer.skewJoin.skewThreshold` (double, default `5.0`) — Skew detection threshold
- `spark.sql.optimizer.skewJoin.saltBuckets` (int, default `10`) — Number of salt buckets

### Expected Functionality

- A join between a 10M-row orders table (where 90% of rows have `customer_id = 1`) and a 1K-row customers table detects skew on `customer_id`
- The optimizer rewrites the join to salt `customer_id` in the orders table and replicate the matching customer row 10 times
- The result contains the same rows as an unoptimized join (correctness preserved)
- For uniform data distributions, the optimizer rule is a no-op (no unnecessary salting)

## Acceptance Criteria

- `SkewDetector` correctly identifies skewed columns from column statistics
- The optimizer rule matches `Join` logical plan nodes and rewrites them when skew is detected
- Salting adds the correct number of buckets and replication matches
- The physical plan executes correctly and produces identical results to a standard sort-merge join
- Non-skewed joins pass through unchanged
- `./build/mvn -DskipTests package` compiles successfully
- `python -m pytest /workspace/tests/test_spark_optimization.py -v --tb=short` passes
