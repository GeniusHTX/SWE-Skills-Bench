# Task: Implement a Partition-Aware Caching Advisor for Spark SQL

## Background

Apache Spark's Catalyst optimizer makes decisions about join strategies, partitioning, and caching, but it does not provide guidance to developers on how to improve their query plans. A new Spark SQL utility module is needed that analyzes a logical or physical query plan, detects common performance anti-patterns (excessive shuffles, skewed joins, redundant computations), and produces actionable optimization recommendations with estimated impact.

## Files to Create/Modify

- `python/pyspark/sql/advisor/__init__.py` (new) — Package init exporting the public API
- `python/pyspark/sql/advisor/analyzer.py` (new) — Plan analyzer that inspects Spark SQL query plans and detects performance anti-patterns
- `python/pyspark/sql/advisor/rules.py` (new) — Rule definitions for detecting shuffle bottlenecks, join skew, missing caching, and partition mismatches
- `python/pyspark/sql/advisor/report.py` (new) — Report generator that formats findings as structured recommendations with severity and estimated impact
- `python/pyspark/sql/advisor/models.py` (new) — Data classes for plan nodes, detected issues, and optimization recommendations
- `python/pyspark/sql/advisor/tests/test_analyzer.py` (new) — Unit tests for the plan analyzer and rule engine

## Requirements

### Plan Analysis

- Accept a Spark DataFrame and extract its physical plan as a string via `df.explain(mode="extended")`
- Parse the plan text to identify node types: `Exchange` (shuffle), `BroadcastHashJoin`, `SortMergeJoin`, `HashAggregate`, `Filter`, `FileScan`, `InMemoryTableScan`
- Build an internal tree representation of the plan nodes with parent-child relationships, preserving node type, output partition count, and estimated row counts where available from the plan text

### Anti-Pattern Detection Rules

- **Excessive Shuffles**: Flag when the plan contains more than 2 `Exchange` nodes; severity "high" if > 4 exchanges
- **Large Table Sort-Merge Join**: Flag `SortMergeJoin` where either input has an `Exchange` with > 200 partitions, suggesting a broadcast join might be more efficient; only flag if the smaller input's estimated size text contains a value under 100MB
- **Redundant Computation**: Flag when the same `FileScan` path appears more than once in the plan, suggesting the DataFrame should be cached or persisted
- **Partition Mismatch**: Flag when an `Exchange` immediately follows another `Exchange` (double shuffle), indicating upstream repartitioning is being undone
- **Missing Filter Pushdown**: Flag when a `Filter` node appears above a `FileScan` that reads Parquet or ORC format, and the filter column matches a partition column listed in the scan's `PartitionFilters` as empty

### Recommendation Report

- Each recommendation includes: `rule_name`, `severity` ("low", "medium", "high"), `location` (plan node description), `description` (what was detected), `suggestion` (actionable fix), `estimated_impact` ("minor", "moderate", "significant")
- The report object has a `to_dict()` method returning a serializable dictionary and a `to_text()` method returning a formatted human-readable string
- Recommendations are sorted by severity (high first) then by estimated impact
- If no issues are detected, the report contains an empty recommendations list and a summary message "No optimization opportunities detected"

### Public API

- `analyze(df: DataFrame) -> Report` — Main entry point that runs all rules against the DataFrame's plan
- `analyze(df: DataFrame, rules: list[str]) -> Report` — Optional rule filter; only run rules whose names are in the list (e.g., `["excessive_shuffles", "redundant_computation"]`)
- If an invalid rule name is passed, raise `ValueError` with message "Unknown rule: {name}. Available rules: {list}"

### Expected Functionality

- A DataFrame with 5 `Exchange` nodes in its plan → report contains an "excessive_shuffles" recommendation with severity "high" and estimated_impact "significant"
- A DataFrame reading the same Parquet path twice → report contains a "redundant_computation" recommendation suggesting `.cache()` or `.persist()`
- A DataFrame plan with `Exchange` directly followed by another `Exchange` → report contains a "partition_mismatch" recommendation
- A clean plan with 1 exchange and no anti-patterns → report summary "No optimization opportunities detected"
- `analyze(df, rules=["nonexistent_rule"])` → `ValueError` with the expected message
- `report.to_dict()` returns a dictionary with keys "recommendations", "summary", "analyzed_at"
- `report.to_text()` returns a multi-line string with severity-sorted recommendations

## Acceptance Criteria

- The analyzer correctly parses Spark physical plan text and identifies node types and their relationships
- All five anti-pattern rules detect their respective issues when present in the plan
- Recommendations include the correct severity, location, description, suggestion, and estimated impact
- The report sorts recommendations by severity and supports both dict and text output formats
- The rule filter parameter correctly limits which rules run and raises `ValueError` for unknown rule names
- Clean plans produce an empty recommendations list with the expected summary message
- Unit tests cover each rule with sample plan text, verify report formatting, and test edge cases
