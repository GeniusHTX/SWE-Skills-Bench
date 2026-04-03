# Task: Implement Data Skew Handling and Partition Optimization Utilities for Apache Spark

## Background

The Apache Spark repository (https://github.com/apache/spark) is a large-scale distributed data processing engine. A new PySpark utility module is needed that provides production-ready solutions for the most common Spark performance problems: data skew in joins, suboptimal partition sizing, inefficient caching strategies, and missing AQE (Adaptive Query Execution) configuration. The utilities must be usable as drop-in replacements for standard Spark operations.

## Files to Create/Modify

- `python/pyspark/sql/optimization/__init__.py` (create) — Package init exporting public API
- `python/pyspark/sql/optimization/skew_handler.py` (create) — Salted join implementation for handling skewed keys
- `python/pyspark/sql/optimization/partition_advisor.py` (create) — Partition size analyzer and repartitioning advisor
- `python/pyspark/sql/optimization/cache_manager.py` (create) — Smart caching utility with storage level selection and invalidation
- `python/pyspark/sql/optimization/config_tuner.py` (create) — AQE and shuffle configuration tuner based on workload profile
- `python/pyspark/tests/test_optimization.py` (create) — Tests using a local SparkSession with synthetic data

## Requirements

### Salted Join (skew_handler.py)

- `salted_join(df_skewed, df_other, key_col, num_salts=10, how="inner")` — performs a join that distributes skewed keys across `num_salts` partitions
  1. Adds a random salt column (integer 0 to `num_salts - 1`) to `df_skewed`
  2. Explodes `df_other` by replicating each row `num_salts` times with each salt value
  3. Joins on `(key_col, salt_col)`
  4. Drops the salt column from the result
- The final result must have identical columns and row semantics as `df_skewed.join(df_other, key_col, how)` — no extra columns, no duplicate rows
- `num_salts` must be ≥ 2; otherwise raise `ValueError`
- `detect_skew(df, key_col, threshold=10.0) -> dict` — computes the ratio of the largest partition size to the median; returns `{"skewed": bool, "skew_ratio": float, "top_keys": list}` where `top_keys` are the top 5 keys by count and `"skewed"` is True when ratio ≥ threshold

### Partition Advisor (partition_advisor.py)

- `PartitionAdvisor` class accepting a `SparkSession`
- `analyze(df) -> dict` — returns `{"num_partitions": int, "partition_sizes_mb": list[float], "min_mb": float, "max_mb": float, "median_mb": float, "recommended_partitions": int}`
- Recommended partitions target 128 MB per partition (configurable via `target_partition_mb: int = 128`)
- `repartition_optimally(df, target_partition_mb=128) -> DataFrame` — repartitions the DataFrame to the recommended count; uses `coalesce` when reducing partitions and `repartition` when increasing
- Must handle empty DataFrames (0 rows) without error, returning them with 1 partition

### Smart Cache Manager (cache_manager.py)

- `CacheManager` class accepting a `SparkSession`
- `smart_cache(df, name: str, storage_level=None) -> DataFrame` — caches the DataFrame with an appropriate storage level; if `storage_level` is None, auto-selects based on estimated size:
  - < 1 GB: `MEMORY_ONLY`
  - 1–10 GB: `MEMORY_AND_DISK`
  - > 10 GB: `DISK_ONLY`
- `invalidate(name: str)` — unpersists the cached DataFrame by name
- `invalidate_all()` — unpersists all managed DataFrames
- `list_cached() -> list[dict]` — returns name, storage level, and whether still cached for each managed DataFrame

### Config Tuner (config_tuner.py)

- `ConfigTuner` class accepting a `SparkSession`
- `apply_profile(profile: str)` — configures the SparkSession for the given workload profile:
  - `"small"` (< 10 GB): shuffle.partitions=50, AQE enabled, broadcast threshold 100 MB
  - `"medium"` (10–100 GB): shuffle.partitions=200, AQE enabled with skew join, Kryo serializer
  - `"large"` (> 100 GB): shuffle.partitions=500, AQE with all optimizations, off-heap memory enabled
- `get_current_config() -> dict` — returns a dict of the current Spark SQL configuration values for the tuned parameters
- Profile must be one of `"small"`, `"medium"`, `"large"`; otherwise raise `ValueError`

### Expected Functionality

- `salted_join` on a DataFrame where one key has 90% of rows produces identical results to a regular join but distributes the skewed key across 10 partitions
- `detect_skew` on a DataFrame with key "A" appearing 1000 times and all other keys appearing 10 times reports `skew_ratio ≈ 100.0` and `skewed=True`
- `PartitionAdvisor.analyze` on a 1 GB DataFrame returns `recommended_partitions ≈ 8` (for 128 MB target)
- `smart_cache` on a 500 MB DataFrame selects `MEMORY_ONLY`; on a 5 GB DataFrame selects `MEMORY_AND_DISK`
- `apply_profile("large")` sets shuffle partitions to 500 and enables AQE

## Acceptance Criteria

- Salted join produces results identical to a standard join for both inner and left join types
- Skew detection correctly identifies skewed keys and reports the skew ratio
- Partition advisor recommends the correct number of partitions for a target size and uses coalesce vs. repartition appropriately
- Cache manager auto-selects storage levels, tracks cached DataFrames, and supports invalidation
- Config tuner applies the correct Spark configuration for each workload profile
- All invalid inputs raise `ValueError` with descriptive messages
- Tests pass using a local SparkSession with synthetic skewed data
