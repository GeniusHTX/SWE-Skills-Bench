# Task: Implement an Adaptive Query Execution Strategy Optimizer for Spark SQL

## Background

Apache Spark (https://github.com/apache/spark) supports Adaptive Query Execution (AQE) that dynamically optimizes query plans at runtime. The task is to implement a custom AQE strategy that detects skewed partitions during shuffle operations, dynamically splits them into smaller sub-partitions, and coalesces under-utilized partitions — all as Spark SQL optimizer rules integrated into the Catalyst framework.

## Files to Create/Modify

- `sql/core/src/main/scala/org/apache/spark/sql/execution/adaptive/SkewedPartitionSplitter.scala` (create) — AQE rule that detects and splits skewed partitions based on runtime statistics
- `sql/core/src/main/scala/org/apache/spark/sql/execution/adaptive/PartitionCoalescer.scala` (create) — AQE rule that coalesces small partitions to reduce task overhead
- `sql/core/src/main/scala/org/apache/spark/sql/execution/adaptive/AdaptiveStrategyOptimizer.scala` (create) — Coordinator that applies both rules in sequence with configurable thresholds
- `sql/core/src/test/scala/org/apache/spark/sql/execution/adaptive/SkewedPartitionSplitterSuite.scala` (create) — Unit tests for skew detection and splitting
- `sql/core/src/test/scala/org/apache/spark/sql/execution/adaptive/PartitionCoalescerSuite.scala` (create) — Unit tests for partition coalescing

## Requirements

### `SkewedPartitionSplitter`

Extends `Rule[SparkPlan]` (a Catalyst rule applied to physical plans).

#### Configuration Parameters
- `skewThresholdBytes` — A partition is considered skewed if its size exceeds this threshold (default: 256 MB, configurable via `spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes`)
- `skewFactor` — A partition is skewed if its size exceeds `skewFactor * medianPartitionSize` (default: 5.0, configurable via `spark.sql.adaptive.skewJoin.skewedPartitionFactor`)
- `maxSplits` — Maximum number of sub-partitions to split a skewed partition into (default: 16)

#### Logic (`apply(plan: SparkPlan): SparkPlan`)
1. Traverse the physical plan tree looking for `ShuffleExchangeExec` nodes
2. For each shuffle exchange, collect runtime partition statistics (size in bytes per partition)
3. Compute the median partition size across all partitions
4. Identify skewed partitions: those exceeding both `skewThresholdBytes` AND `skewFactor * medianSize`
5. For each skewed partition, calculate the number of splits: `min(ceil(partitionSize / medianSize), maxSplits)`
6. Replace the shuffle exchange with a `SkewedShuffleExec` node that reads the skewed partition in parallel sub-tasks
7. Return the modified plan; non-skewed partitions remain unchanged

#### Skew Detection Results
Produce a `SkewReport` case class for each shuffle:
```scala
case class SkewReport(
    shuffleId: Int,
    totalPartitions: Int,
    skewedPartitions: Seq[SkewedPartitionInfo],
    medianSizeBytes: Long,
    maxSizeBytes: Long
)

case class SkewedPartitionInfo(
    partitionId: Int,
    sizeBytes: Long,
    numSplits: Int
)
```

### `PartitionCoalescer`

Extends `Rule[SparkPlan]`.

#### Configuration Parameters
- `targetPartitionSizeBytes` — Target size for coalesced partitions (default: 64 MB, configurable via `spark.sql.adaptive.coalescePartitions.targetSizeInBytes`)
- `minPartitions` — Minimum number of partitions to maintain after coalescing (default: 1, configurable via `spark.sql.adaptive.coalescePartitions.minPartitionNum`)

#### Logic (`apply(plan: SparkPlan): SparkPlan`)
1. Traverse the plan tree looking for `ShuffleExchangeExec` nodes
2. Collect runtime partition sizes
3. Use a greedy bin-packing algorithm: iterate through partitions in order, accumulate consecutive partitions into a group until adding the next partition would exceed `targetPartitionSizeBytes`
4. Ensure the resulting number of partitions is at least `minPartitions`
5. Replace the shuffle exchange with a `CoalescedShuffleExec` node that reads multiple original partitions in a single task
6. Return the modified plan

### `AdaptiveStrategyOptimizer`

#### Logic
1. Apply `SkewedPartitionSplitter` first (split large partitions)
2. Apply `PartitionCoalescer` second (merge small partitions)
3. Log the transformations: number of partitions split, number of partitions coalesced
4. Return the final optimized plan

#### Integration Point
- Register as an additional AQE optimizer rule via `spark.sql.adaptive.customOptimizedRules`

## Expected Functionality

- Given a shuffle with 200 partitions where partition 42 is 2 GB and the median is 50 MB:
  - `SkewedPartitionSplitter` detects partition 42 as skewed (2 GB > 256 MB AND 2 GB > 5 × 50 MB)
  - Splits partition 42 into `min(ceil(2048/50), 16) = 16` sub-partitions
  - Other partitions remain unchanged

- Given a shuffle with 1000 partitions averaging 5 MB each:
  - `PartitionCoalescer` with target 64 MB merges roughly 12-13 consecutive partitions per group
  - Results in approximately 77-84 coalesced partitions

- `AdaptiveStrategyOptimizer` applies both rules and logs the result

## Acceptance Criteria

- `SkewedPartitionSplitter` correctly identifies skewed partitions using both absolute threshold and median-relative factor
- Skewed partitions are split into the calculated number of sub-partitions (bounded by `maxSplits`)
- `PartitionCoalescer` groups consecutive partitions to approach `targetPartitionSizeBytes` without exceeding it
- Coalescing maintains at least `minPartitions` output partitions
- Both rules only modify `ShuffleExchangeExec` nodes; other plan nodes pass through unchanged
- `SkewReport` accurately reflects the detected skew pattern
- Configuration parameters are read from Spark SQL conf with the specified config keys
- All test suites pass with synthetic partition statistics
