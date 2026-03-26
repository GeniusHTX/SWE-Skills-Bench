# Task: Implement Spark Job Optimization for Large-Scale Join and Aggregation Pipeline

## Background

Apache Spark (https://github.com/apache/spark) is a distributed computing framework. The project needs an optimized Spark job that processes a large-scale data pipeline involving multi-table joins, aggregations, and window functions. The job must be tuned for performance with proper partitioning, join strategies, AQE (Adaptive Query Execution) configuration, and caching.

## Files to Create/Modify

- `examples/src/main/scala/org/apache/spark/examples/sql/OptimizedPipeline.scala` (create) — Optimized Spark SQL pipeline with joins, aggregations, and window functions
- `examples/src/main/scala/org/apache/spark/examples/sql/PipelineConfig.scala` (create) — Configuration for partitioning, memory, and AQE settings
- `examples/src/main/scala/org/apache/spark/examples/sql/PipelineMetrics.scala` (create) — Metrics collection for benchmarking pipeline stages
- `examples/src/test/scala/org/apache/spark/examples/sql/OptimizedPipelineSuite.scala` (create) — Tests for pipeline correctness and optimization verification

## Requirements

### Data Pipeline

- The pipeline processes three input datasets:
  - `transactions` — ~100M rows: `transaction_id`, `user_id`, `product_id`, `amount`, `timestamp`, `region`
  - `users` — ~10M rows: `user_id`, `name`, `signup_date`, `tier` (one of "free", "premium", "enterprise")
  - `products` — ~1M rows: `product_id`, `category`, `price`, `vendor_id`
- Pipeline stages:
  1. **Join**: Join transactions with users and products on their respective IDs
  2. **Filter**: Remove transactions older than a configurable date and users in "free" tier
  3. **Aggregate**: Compute per-user, per-category metrics: total_spend, transaction_count, avg_amount
  4. **Window**: Rank users by total_spend within each category using `dense_rank()` over a window partitioned by category ordered by total_spend DESC
  5. **Output**: Write the top 100 users per category to Parquet format, partitioned by `region` and `category`

### Join Optimization

- Use broadcast join for `products` (small dimension table, < 100MB): `transactions.join(broadcast(products), "product_id")`
- Use sort-merge join for `transactions` and `users` (both large)
- Repartition `transactions` by `user_id` before the join with `users` to ensure data locality
- Set `spark.sql.autoBroadcastJoinThreshold` to `100MB` in the config
- After joining, coalesce the result to reduce the number of partitions if the filtered dataset is significantly smaller

### Partition Tuning

- Set `spark.sql.shuffle.partitions` based on data size: `max(200, estimated_data_size_mb / 128)` — aim for ~128MB per partition
- After the filter stage, repartition by `(user_id, category)` to optimize the subsequent group-by aggregation
- For the output write, use `repartition("region", "category")` to produce well-organized Parquet files

### AQE Configuration

- Enable Adaptive Query Execution: `spark.sql.adaptive.enabled = true`
- Enable coalescing shuffle partitions: `spark.sql.adaptive.coalescePartitions.enabled = true` with `minPartitionSize = 64MB`
- Enable skew join optimization: `spark.sql.adaptive.skewJoin.enabled = true` with `skewedPartitionThresholdInBytes = 256MB`
- Enable local shuffle reader: `spark.sql.adaptive.localShuffleReader.enabled = true`

### Caching Strategy

- Cache the joined and filtered dataset (`joinedAndFiltered.cache()`) since it's used for both aggregation and a potential secondary output
- Use `MEMORY_AND_DISK` storage level for the cache
- Unpersist the cached DataFrame after the pipeline completes to free memory
- Do NOT cache intermediate DataFrames that are only used once

### Metrics Collection

- Record wall-clock time for each pipeline stage (join, filter, aggregate, window, write)
- Record the number of output rows after each stage
- Record the number of shuffle partitions used (from Spark's query plan)
- Provide a `PipelineMetrics` case class with: `stage_name`, `duration_ms`, `input_rows`, `output_rows`, `shuffle_partitions`
- Log a summary report at the end of the pipeline

### Expected Functionality

- The pipeline processes the three datasets and produces Parquet output partitioned by region and category
- Broadcast join is used for products (visible in the explain plan as `BroadcastHashJoin`)
- The pipeline benefits from AQE: coalesced shuffle partitions and skew join handling
- Caching the filtered join result avoids recomputing it for secondary outputs
- The top 100 users per category are correctly ranked using `dense_rank()`
- Metrics report shows timing for each stage

## Acceptance Criteria

- The pipeline implements all 5 stages (join, filter, aggregate, window, output) correctly
- `products` join uses broadcast join (verify via explain plan containing `BroadcastHashJoin`)
- `transactions` is repartitioned by `user_id` before the sort-merge join with `users`
- AQE configuration enables partition coalescing, skew join handling, and local shuffle reader
- Shuffle partition count is computed from data size, not hardcoded
- The joined-and-filtered DataFrame is cached with `MEMORY_AND_DISK` and unpersisted after use
- Window function uses `dense_rank()` partitioned by category and ordered by total_spend DESC
- Output is written as Parquet partitioned by `region` and `category`
- `PipelineMetrics` records and reports timing and row counts per stage
- Tests verify correct output (aggregations, rankings) and that the explain plan shows expected join strategies
