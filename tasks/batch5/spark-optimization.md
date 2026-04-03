# Task: Optimize Spark SQL Query Performance for Large-Scale Aggregations

## Background

Apache Spark (https://github.com/apache/spark) is a distributed computing framework. This task requires implementing Spark SQL query optimizations for a data pipeline processing a large sales dataset: partition pruning, broadcast join optimization, adaptive query execution tuning, and custom UDFs. The pipeline computes daily revenue aggregations with dimensional joins.

## Files to Create/Modify

- `examples/src/main/scala/org/apache/spark/examples/sql/SalesAggregation.scala` (create) — Spark application implementing the sales aggregation pipeline with optimized query patterns.
- `examples/src/main/scala/org/apache/spark/examples/sql/SalesOptimizer.scala` (create) — Utility object containing optimization configurations, custom partitioner, and broadcast join helper.
- `examples/src/main/scala/org/apache/spark/examples/sql/SalesUDFs.scala` (create) — Custom UDFs: `fiscal_quarter(date)`, `revenue_bucket(amount)`, and `product_category_rollup(category, subcategory)`.
- `examples/src/test/scala/org/apache/spark/examples/sql/SalesAggregationSuite.scala` (create) — Tests validating aggregation correctness, partition pruning, and UDF outputs.

## Requirements

### Data Model

- **sales** table (parquet, partitioned by `sale_date`): `sale_id` (long), `sale_date` (date), `product_id` (int), `customer_id` (int), `quantity` (int), `unit_price` (decimal), `discount` (decimal), `region` (string).
- **products** table (parquet, small — ~10,000 rows): `product_id` (int), `name` (string), `category` (string), `subcategory` (string), `cost` (decimal).
- **customers** table (parquet, small — ~100,000 rows): `customer_id` (int), `name` (string), `segment` (string), `country` (string).

### Aggregation Pipeline

The pipeline computes a daily revenue report:
1. Filter sales to a date range (leverage partition pruning on `sale_date`).
2. Join sales with products (broadcast join — products is small).
3. Join with customers (broadcast join — customers is small enough).
4. Compute: `revenue = quantity * unit_price * (1 - discount)`, `profit = revenue - (quantity * cost)`.
5. Aggregate by `sale_date`, `region`, `category`, `customer_segment`:
   - `total_revenue`, `total_profit`, `order_count`, `avg_order_value`, `unique_customers`.
6. Apply UDFs: `fiscal_quarter(sale_date)`, `revenue_bucket(total_revenue)`.
7. Write results partitioned by `fiscal_quarter`.

### Optimization Configurations (`SalesOptimizer`)

- Enable AQE: `spark.sql.adaptive.enabled = true`.
- Set `spark.sql.adaptive.coalescePartitions.enabled = true`, `spark.sql.adaptive.coalescePartitions.minPartitionSize = 64MB`.
- Set `spark.sql.adaptive.skewJoin.enabled = true`, `spark.sql.adaptive.skewJoin.skewedPartitionFactor = 5`.
- Broadcast threshold: `spark.sql.autoBroadcastJoinThreshold = 50MB`.
- `optimizeSession(spark: SparkSession)` — applies all settings.
- `repartitionForWrite(df: DataFrame, partitionColumns: Seq[String], targetPartitionSize: String)` — repartitions the output to avoid small files.

### Custom UDFs

- `fiscal_quarter(date: Date): String` — returns "Q1 FY2024" format. Fiscal year starts April 1: Jan-Mar = Q4 of prior FY, Apr-Jun = Q1, Jul-Sep = Q2, Oct-Dec = Q3.
- `revenue_bucket(amount: BigDecimal): String` — returns "0-100", "100-500", "500-1K", "1K-5K", "5K-10K", "10K+" based on the amount.
- `product_category_rollup(category: String, subcategory: String): String` — returns `"category > subcategory"` or just `category` if subcategory is null.

### Performance Requirements

- The query plan must show `BroadcastHashJoin` for both dimension table joins (not `SortMergeJoin`).
- Partition pruning must be visible in the query plan for the date filter (predicate pushdown on `sale_date`).
- Output files should be ~128MB each (controlled by coalescing).

### Expected Functionality

- Processing 1 month of sales data (31 partitions, ~10M rows) → produces aggregation output partitioned by fiscal quarter.
- `fiscal_quarter(Date("2024-01-15"))` → `"Q4 FY2024"` (Jan = Q4 of FY ending Mar 2024).
- `fiscal_quarter(Date("2024-04-01"))` → `"Q1 FY2025"`.
- `revenue_bucket(BigDecimal("750.00"))` → `"500-1K"`.
- The explain plan shows `BroadcastHashJoin` and `PartitionFilters` on `sale_date`.

## Acceptance Criteria

- The pipeline compiles with `./build/mvn compile -pl examples -DskipTests`.
- Broadcast joins are used for both dimension tables (verified in explain plan).
- Partition pruning is applied on the `sale_date` filter.
- AQE settings are configured for coalescing and skew handling.
- All three UDFs produce correct outputs for test inputs.
- Aggregation correctly computes revenue, profit, and all metrics.
- Output is partitioned by fiscal quarter with reasonable file sizes.
- Tests validate UDF outputs, aggregation correctness with sample data, and join strategy in the query plan.
