# Task: Optimize a PySpark ETL Pipeline for a Clickstream Data Warehouse

## Background

A daily clickstream ETL pipeline processes 500GB of raw JSON event data from S3, joins it with user and product dimension tables, computes session-level aggregations, and writes partitioned Parquet output. The current pipeline takes 4.5 hours and frequently fails with OOM errors. Optimize the Spark configuration, fix data skew issues, implement proper partitioning, use broadcast joins, add caching, and convert the heaviest aggregation to an incremental merge pattern.

## Files to Create/Modify

- `etl/spark_config.py` (create) — Optimized SparkSession builder with tuned configuration parameters
- `etl/jobs/clickstream_daily.py` (create) — Main ETL job: ingest JSON, join dimensions, sessionize, aggregate, write Parquet
- `etl/jobs/session_aggregation.py` (create) — Session-level aggregation with skew handling using salted keys
- `etl/jobs/incremental_merge.py` (create) — Incremental merge of daily aggregated data into the cumulative facts table
- `etl/utils/partition_utils.py` (create) — Utility functions for calculating optimal partition counts and repartitioning strategies
- `etl/utils/skew_handler.py` (create) — Salted join implementation for handling skewed user_id keys
- `etl/quality/data_checks.py` (create) — Post-ETL data quality checks using Spark SQL assertions

## Requirements

### Spark Configuration (`etl/spark_config.py`)

`create_spark_session(app_name: str, env: str = "production") -> SparkSession`:

```python
spark = (SparkSession.builder
    .appName(app_name)
    # Adaptive Query Execution
    .config("spark.sql.adaptive.enabled", "true")
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
    .config("spark.sql.adaptive.coalescePartitions.minPartitionSize", "64MB")
    .config("spark.sql.adaptive.skewJoin.enabled", "true")
    .config("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5")
    .config("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB")
    # Shuffle
    .config("spark.sql.shuffle.partitions", "400")
    .config("spark.shuffle.compress", "true")
    .config("spark.shuffle.spill.compress", "true")
    # Serialization
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
    .config("spark.kryoserializer.buffer.max", "512m")
    # Memory
    .config("spark.executor.memory", "8g")
    .config("spark.executor.memoryOverhead", "2g")
    .config("spark.driver.memory", "4g")
    .config("spark.memory.fraction", "0.8")
    .config("spark.memory.storageFraction", "0.3")
    # Broadcast
    .config("spark.sql.autoBroadcastJoinThreshold", "50MB")
    # Parquet
    .config("spark.sql.parquet.compression.codec", "zstd")
    .config("spark.sql.parquet.mergeSchema", "false")
    .config("spark.sql.parquet.filterPushdown", "true")
    # Dynamic allocation
    .config("spark.dynamicAllocation.enabled", "true")
    .config("spark.dynamicAllocation.minExecutors", "10")
    .config("spark.dynamicAllocation.maxExecutors", "100")
    .config("spark.dynamicAllocation.executorIdleTimeout", "60s")
    .getOrCreate())
```

### Main ETL Job (`etl/jobs/clickstream_daily.py`)

`run_daily_etl(spark: SparkSession, date: str) -> None`:

1. **Ingest**: Read raw JSON from `s3://data-lake/raw/clickstream/date={date}/` with explicit schema (don't infer). Schema: `event_id: string`, `user_id: string`, `product_id: string`, `event_type: string`, `timestamp: long`, `session_id: string`, `page_url: string`, `referrer: string`, `device_type: string`, `properties: map<string,string>`.

2. **Filter early**: Drop events where `event_type` is `heartbeat` or `ping` (reduces volume by ~30%). Drop `properties` column if not needed downstream. Apply `filter(col("user_id").isNotNull())`.

3. **Join dimensions**:
   - **Users**: Read `s3://data-lake/dimensions/users/` (Parquet, ~50MB). Broadcast join on `user_id`. Select `user_id`, `country`, `signup_date`, `account_tier`.
   - **Products**: Read `s3://data-lake/dimensions/products/` (Parquet, ~20MB). Broadcast join on `product_id`. Select `product_id`, `category`, `subcategory`, `price`.

4. **Sessionize**: Group events by `session_id`. Calculate `session_start` (min timestamp), `session_end` (max timestamp), `session_duration_seconds`, `event_count`, `page_views` (count where event_type='page_view'), `add_to_carts` (count where event_type='add_to_cart'), `purchases` (count where event_type='purchase').

5. **Write**: Write sessionized data to `s3://data-lake/processed/sessions/date={date}/` as Parquet partitioned by `country` and `device_type`. Use `coalesce` to target ~256MB per output file.

### Session Aggregation with Skew Handling (`etl/jobs/session_aggregation.py`)

Problem: 5% of user_ids generate 40% of events (bot accounts, power users). This causes data skew in the `groupBy("user_id")` aggregation.

`aggregate_user_sessions(spark: SparkSession, sessions_df: DataFrame) -> DataFrame`:

1. Detect skewed keys: `sessions_df.groupBy("user_id").count().filter("count > 10000")` → collect as skewed_users set.
2. Split into `normal_df` (user_id NOT in skewed set) and `skewed_df`.
3. For `skewed_df`: add salt column `F.concat(col("user_id"), F.lit("_"), (F.rand() * 10).cast("int"))` → groupBy salted key → aggregate → groupBy original user_id → re-aggregate.
4. For `normal_df`: standard groupBy `user_id` → aggregate.
5. Union both results.

Aggregations per user:
- `total_sessions`, `total_events`, `total_page_views`, `total_purchases`, `total_session_duration_seconds`, `avg_session_duration_seconds`, `first_session_date`, `last_session_date`, `distinct_products_viewed`, `distinct_categories_browsed`.

### Incremental Merge (`etl/jobs/incremental_merge.py`)

`merge_daily_into_cumulative(spark: SparkSession, daily_df: DataFrame, date: str) -> None`:

- Read existing cumulative table from `s3://data-lake/warehouse/user_activity/`.
- Merge daily aggregates into cumulative:
  - For existing user_ids: update `total_sessions += daily.total_sessions`, `total_events += daily.total_events`, update `last_session_date`, recalculate averages.
  - For new user_ids: insert new rows.
- Write back using Delta Lake format with `mergeSchema` option.
- If Delta is unavailable, implement with a full outer join + coalesce pattern writing partitioned Parquet with overwrite on affected date partitions.

### Partition Utilities (`etl/utils/partition_utils.py`)

- `calculate_optimal_partitions(df: DataFrame, target_partition_mb: int = 128) -> int`: Estimate DataFrame size using `spark.sessionState.executePlan`, compute partition count.
- `repartition_for_write(df: DataFrame, target_file_mb: int = 256, partition_cols: list = None) -> DataFrame`: Repartition or coalesce to achieve target file sizes, optionally preserving partition columns.
- `analyze_partition_skew(df: DataFrame, partition_col: str) -> DataFrame`: Return statistics on partition sizes (min, max, mean, stddev, skew coefficient) to detect problematic skew.

### Skew Handler (`etl/utils/skew_handler.py`)

- `salted_join(left_df: DataFrame, right_df: DataFrame, join_col: str, num_salts: int = 10, join_type: str = "inner") -> DataFrame`:
  - Add salt to left (skewed) side: `salt = (F.rand() * num_salts).cast("int")`, create `salted_key = concat(join_col, "_", salt)`.
  - Explode right side with all salt values (0 to num_salts-1): `exploded_key = concat(join_col, "_", salt_value)`.
  - Join on salted keys.
  - Drop salt columns from output.

- `detect_skew(df: DataFrame, key_col: str, threshold_factor: float = 5.0) -> list[str]`: Identify keys where count > threshold_factor × median count.

### Data Quality Checks (`etl/quality/data_checks.py`)

`run_quality_checks(spark: SparkSession, output_path: str, date: str) -> dict`:

- **Completeness**: count rows, assert > 0. Count null `session_id` rows, assert == 0.
- **Uniqueness**: count distinct `session_id` == total count (no duplicates).
- **Freshness**: max `session_end` timestamp within expected date range.
- **Volume**: row count within ±20% of 7-day rolling average (detect anomalies).
- **Value range**: `session_duration_seconds >= 0` and `< 86400` (no negative or >24h sessions).
- **Referential integrity**: all `user_id` values exist in the users dimension table.
- Return dict: `{"passed": [...], "failed": [...], "warnings": [...]}`.

### Expected Functionality

- Pipeline processes 500GB of JSON clickstream data, joins with broadcast dimensions, handles skewed user_ids via salting.
- Output sessions are written as zstd-compressed Parquet partitioned by `country/device_type`.
- Incremental merge updates cumulative user activity table without reprocessing historical data.
- Data quality checks validate completeness, uniqueness, freshness, volume, and referential integrity.
- Runtime target: under 90 minutes (down from 4.5 hours).

## Acceptance Criteria

- Spark session enables AQE (adaptive query execution) with skew join handling, dynamic allocation (10-100 executors), Kryo serialization, and zstd Parquet compression.
- Raw JSON ingestion uses explicit schema (no schema inference) and filters irrelevant events early before joins.
- Dimension joins use `F.broadcast()` for tables under 50MB (users ~50MB, products ~20MB).
- Session aggregation detects skewed user_ids (>10K events) and applies salted key strategy with salt factor 10.
- Salted join utility adds salt to skewed side and explodes the smaller side, joining on salted keys.
- Incremental merge combines daily aggregates into cumulative table using upsert logic (update existing + insert new).
- Partition utility calculates optimal partition count based on DataFrame size targeting 128MB partitions.
- Output is coalesced to target ~256MB per file and partitioned by `country` and `device_type`.
- Data quality checks run post-ETL and validate row count, null rates, uniqueness, date range, value ranges, and referential integrity.
- Dynamic allocation scales executors between 10 and 100 based on workload.
