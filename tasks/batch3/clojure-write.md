# Task: Implement a Clojure Data Pipeline Module for Metabase Query Preprocessing

## Background

Metabase (https://github.com/metabase/metabase) is an open-source business intelligence tool built with Clojure. The query execution pipeline needs a new preprocessing module that normalizes, validates, and transforms user queries before they reach the database driver. This module should follow Metabase's conventions: bottom-up development with REPL-driven workflow, functional data transformation, and integration with the `metabase.query-processor` namespace.

## Files to Create/Modify

- `src/metabase/query_processor/preprocess.clj` (create) — Query preprocessing pipeline: normalization, validation, and transformation
- `src/metabase/query_processor/preprocess/normalize.clj` (create) — Query normalization functions
- `src/metabase/query_processor/preprocess/validate.clj` (create) — Query validation with error reporting
- `test/metabase/query_processor/preprocess_test.clj` (create) — Tests for the preprocessing pipeline

## Requirements

### Query Normalization

- Implement `normalize-query` function that takes a raw query map and normalizes it:
  - Convert all keyword keys to `kebab-case` (e.g., `:source_table` → `:source-table`)
  - Remove `nil`-valued entries recursively through nested maps
  - Normalize `:order-by` clauses: convert shorthand `[:field-id 1]` to full form `[:asc [:field-id 1]]`
  - Normalize date filter values: convert string dates to Metabase's internal format `[:absolute-datetime "2024-01-01" :day]`
  - Deduplicate `:fields` entries (same field referenced multiple times)
- The normalization must be idempotent: `(= (normalize-query q) (normalize-query (normalize-query q)))`

### Query Validation

- Implement `validate-query` function that checks:
  - `:source-table` is present and is a positive integer
  - `:fields` entries (if present) are valid field references: `[:field-id pos-int?]` or `[:field-literal string? keyword?]`
  - `:filter` clauses use valid operators: `:=`, `:!=`, `:<`, `:>`, `:<=`, `:>=`, `:between`, `:contains`, `:starts-with`, `:ends-with`, `:is-null`, `:not-null`
  - `:limit` (if present) is a positive integer ≤ 10000
  - `:order-by` clauses reference fields that exist in `:fields` (if `:fields` is specified)
- Return `{:valid true}` or `{:valid false, :errors [{:type :invalid-field, :message "...", :path [:filter 0 :field]}]}`
- Collect all errors (don't stop at the first one)

### Query Transformation Pipeline

- Implement `preprocess` as a pipeline of transformations applied in order:
  1. `normalize-query` — normalize the raw input
  2. `validate-query` — validate the normalized query; short-circuit if invalid
  3. `add-default-limit` — if no `:limit` is specified, add `:limit 2000`
  4. `add-default-order` — if no `:order-by` is specified and `:source-table` has a primary key, add `[:asc [:field-id pk]]`
  5. `expand-wildcards` — if `:fields` is `[:*]` or absent, resolve to the full list of field IDs for the source table (requires a field resolver function parameter)
- The pipeline is implemented using `comp` or Clojure's threading macros
- Each step is a pure function (except `expand-wildcards` which takes a field resolver)
- The field resolver is passed as a parameter: `(preprocess query {:field-resolver resolver-fn})`

### Error Handling

- Invalid queries should produce a data structure describing all errors, not throw exceptions
- If a transformation step encounters an issue it can handle (e.g., unknown field in order-by), it should remove the problematic clause and add a `:warnings` entry to the query metadata
- Fatal validation errors (missing `:source-table`) prevent further processing and return immediately

### Expected Functionality

- `(normalize-query {:source_table 1, :fields [[:field-id 1] [:field-id 1]], :order-by [[:field-id 2]], :extra nil})` → `{:source-table 1, :fields [[:field-id 1]], :order-by [[:asc [:field-id 2]]]}`
- `(validate-query {:source-table 1, :filter [:= [:field-id 1] 42]})` → `{:valid true}`
- `(validate-query {:filter [:= [:field-id 1] 42]})` → `{:valid false, :errors [{:type :missing-source-table ...}]}`
- `(validate-query {:source-table 1, :limit -5})` → `{:valid false, :errors [{:type :invalid-limit ...}]}`
- `(preprocess {:source_table 1} {:field-resolver (fn [table-id] [[:field-id 1] [:field-id 2]])})` → `{:source-table 1, :fields [[:field-id 1] [:field-id 2]], :limit 2000, :order-by [[:asc [:field-id 1]]]}`
- Double normalization produces identical output (idempotent)

## Acceptance Criteria

- `normalize-query` converts key format, removes nils, normalizes order-by shorthand, deduplicates fields, and is idempotent
- `validate-query` checks source-table, field references, filter operators, limit, and order-by field existence; returns all errors
- The preprocessing pipeline applies all steps in order and short-circuits on validation failure
- Default limit (2000) and default order-by (primary key ascending) are added when not specified
- Field wildcard expansion calls the provided resolver function
- Non-fatal issues produce warnings instead of errors
- Fatal validation errors (missing source-table) prevent further processing
- Tests cover normalization, each validation rule, the full pipeline, default values, wildcard expansion, and idempotency
