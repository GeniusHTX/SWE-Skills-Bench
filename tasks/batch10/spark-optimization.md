# Task: Implement Adaptive Partitioning and Skew-Resistant Join Optimizer for Spark SQL

## Background

Apache Spark's `sql/catalyst/` optimizer and `sql/core/` execution engine need a new physical plan optimization rule that detects partition skew at plan time using table statistics, rewrites skewed sort-merge joins into salted joins, and dynamically selects broadcast vs. sort-merge vs. bucket join strategies based on estimated data sizes. The implementation must plug into Catalyst's existing rule-based optimizer in `sql/catalyst/src/` and the physical planning layer in `sql/core/src/`.

## Files to Create/Modify

- `sql/catalyst/src/main/scala/org/apache/spark/sql/catalyst/optimizer/SkewJoinOptimizationRule.scala` (new) — Catalyst optimizer rule that analyzes join key statistics, detects skew using a configurable skew factor threshold, and rewrites the logical plan to insert salting operations
- `sql/catalyst/src/main/scala/org/apache/spark/sql/catalyst/optimizer/AdaptivePartitionEstimator.scala` (new) — Estimates optimal partition count from table byte sizes and a target partition size in MB, provides helper to compute partition skew ratio from column statistics
- `sql/core/src/main/scala/org/apache/spark/sql/execution/joins/SkewedSortMergeJoinExec.scala` (new) — Physical execution node for skew-handled sort-merge join: splits hot partitions into sub-partitions, replicates the small side for those keys, and merges results
- `sql/core/src/main/scala/org/apache/spark/sql/execution/adaptive/DynamicJoinSelection.scala` (new) — AQE runtime rule that checks actual shuffle partition sizes post-map and switches a sort-merge join to broadcast if one side's materialized size falls below the broadcast threshold
- `sql/catalyst/src/test/scala/org/apache/spark/sql/catalyst/optimizer/SkewJoinOptimizationRuleSuite.scala` (new) — Unit tests for the skew detection and rewrite rule
- `sql/core/src/test/scala/org/apache/spark/sql/execution/joins/SkewedSortMergeJoinExecSuite.scala` (new) — Unit tests for the physical skew join execution

## Requirements

### SkewJoinOptimizationRule

- Extend `org.apache.spark.sql.catalyst.rules.Rule[LogicalPlan]`
- Trigger only on `Join` nodes where the join type is `Inner`, `LeftOuter`, or `RightOuter`
- Read column-level statistics (`ColumnStat`) for join keys from the logical plan's `Statistics`; if statistics are unavailable, skip rewriting
- Detect skew when `max_key_frequency / avg_key_frequency > skewFactor` (configurable via `spark.sql.optimizer.skewJoin.skewFactor`, default `5.0`)
- When skew is detected, rewrite the plan to:
  1. Add a `Project` that appends a `salt` column (`rand() * numSalts` cast to `IntegerType`) to the skewed side
  2. Add a `Generate` (explode) on the non-skewed side producing rows for each salt value in `[0, numSalts)`
  3. Replace the join key with `concat(original_key, "_", salt)`
  4. Wrap the output in a `Project` that drops the salt column
- Accept `spark.sql.optimizer.skewJoin.numSalts` (default `10`) and `spark.sql.optimizer.skewJoin.enabled` (default `true`)

### AdaptivePartitionEstimator

- Provide `estimatePartitions(dataSizeBytes: Long, targetPartitionSizeMB: Int = 128): Int` returning `max(ceil(dataSize / targetSize), 1)`
- Provide `computeSkewRatio(columnStats: ColumnStat): Double` returning `maxFrequency / avgFrequency` from histogram data; return `1.0` if no histogram is available
- Provide `recommendRepartition(dataSizeBytes: Long, currentPartitions: Int, targetPartitionSizeMB: Int): Option[Int]` — return `Some(newCount)` only if the current count differs from the estimated count by more than 20%

### SkewedSortMergeJoinExec

- Extend `SparkPlan` as a `BinaryExecNode`
- Accept `left: SparkPlan`, `right: SparkPlan`, `joinKeys: Seq[Expression]`, `skewedKeys: Set[Any]`, `numSplits: Int`
- During `doExecute()`:
  - For keys in `skewedKeys`, split the left partition into `numSplits` sub-partitions using key hash modulo
  - Replicate corresponding right-side rows for each sub-partition
  - Perform sort-merge join on each sub-pair
  - Union all sub-results
- For non-skewed keys, execute a standard sort-merge join
- Override `outputPartitioning` to return `HashPartitioning` on the original join keys

### DynamicJoinSelection

- Implement as an `AQE` post-shuffle rule that receives `ShuffleQueryStageExec` instances with materialized statistics
- If one side of a sort-merge join has a total materialized size below `spark.sql.autoBroadcastJoinThreshold` (default `10MB`), replace the `SortMergeJoinExec` with `BroadcastHashJoinExec`
- If both sides exceed the broadcast threshold but partition skew is detected (largest partition > `5 × median`), inject a `CoalescePartitions` operation to split the oversized partitions
- Log the join strategy switch at `INFO` level via Spark's internal logging

### Expected Functionality

- A join between a 100GB table and a 5MB dimension table where AQE detects the dimension table's shuffle output is 5MB → runtime switch to broadcast hash join
- A join on `customer_id` where 60% of rows have `customer_id = "ACME"` and skew factor is set to 5 → the ACME key is salted into 10 sub-keys, non-ACME keys pass through unmodified
- `estimatePartitions(dataSizeBytes = 10737418240L, targetPartitionSizeMB = 128)` → returns `80`
- `estimatePartitions(dataSizeBytes = 0L)` → returns `1`
- `recommendRepartition(dataSizeBytes = 10GB, currentPartitions = 200, targetPartitionSizeMB = 128)` → returns `Some(80)` since 200 differs from 80 by more than 20%
- `recommendRepartition(dataSizeBytes = 25GB, currentPartitions = 200, targetPartitionSizeMB = 128)` → returns `None` since estimate ≈ 200
- Skew optimization rule with `spark.sql.optimizer.skewJoin.enabled = false` → rule is a no-op, plan unchanged
- Skew optimization rule on a join with no column statistics → plan unchanged, no rewriting
- `SkewedSortMergeJoinExec` with `skewedKeys = Set("ACME")` on a dataset where ACME accounts for 10M rows → produces correct join results identical to a standard sort-merge join

## Acceptance Criteria

- `./build/mvn -DskipTests package` completes successfully with the new files compiled
- `./build/mvn -pl sql/catalyst -Dtest=SkewJoinOptimizationRuleSuite test` passes all tests
- `./build/mvn -pl sql/core -Dtest=SkewedSortMergeJoinExecSuite test` passes all tests
- The skew rewrite rule correctly injects salting for join keys whose frequency exceeds the skew factor
- The rewrite preserves join correctness: salted join output matches standard sort-merge join output row-for-row
- Non-skewed keys are not affected by the salting rewrite
- DynamicJoinSelection correctly downgrades to broadcast when post-shuffle statistics show a small table
- Partition estimator returns `1` for zero-byte input and correct values for multi-GB inputs
- All new Scala files compile against Spark's existing dependencies without adding new library dependencies
