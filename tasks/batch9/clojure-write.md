# Task: Implement a Data Migration Validator in Clojure for Metabase

## Background

Metabase (https://github.com/metabase/metabase) frequently runs data migrations when upgrading database schemas. A new migration validation system is needed in Clojure that can analyze database table structures before and after migrations, detect schema drift, validate data integrity constraints, and generate reports. The implementation must follow Metabase's REPL-driven development workflow, Clojure coding conventions, and functional programming principles.

## Files to Create/Modify

- `src/metabase/migration_validator/core.clj` (create) — Main namespace with public API: `validate-migration`, `compare-schemas`, `generate-report`
- `src/metabase/migration_validator/schema_diff.clj` (create) — Schema comparison logic: column additions/removals/type-changes detection between two schema snapshots
- `src/metabase/migration_validator/integrity.clj` (create) — Data integrity checks: null constraint violations, foreign key orphans, unique constraint duplicates
- `src/metabase/migration_validator/report.clj` (create) — Report generation in EDN and Markdown formats
- `test/metabase/migration_validator/core_test.clj` (create) — Tests using `deftest` and `is` macros covering all validation scenarios

## Requirements

### Schema Snapshot Format

- A schema snapshot is an EDN map: `{:tables {"users" {:columns {"id" {:type :bigint :nullable false :primary-key true} "name" {:type :varchar :nullable false} "email" {:type :varchar :nullable true :unique true}}} "orders" {:columns {...}}}}`
- Each column map must include `:type` (keyword), `:nullable` (boolean), and optionally `:primary-key`, `:unique`, `:default`, `:foreign-key` (reference as `{:table "other" :column "id"}`)

### Schema Diff (`schema_diff.clj`)

- `(compare-schemas before after)` returns a map of changes per table:
  - `:added-tables` — Set of table names present in `after` but not `before`
  - `:removed-tables` — Set of table names present in `before` but not `after`
  - `:modified-tables` — Map of table name to `{:added-columns {...} :removed-columns {...} :type-changes {...} :nullable-changes {...}}`
- `:type-changes` is a map of column name to `{:before :varchar :after :text}`
- `:nullable-changes` is a map of column name to `{:before true :after false}` (nullable → non-nullable is a breaking change)
- The function must be pure — no side effects, no database access

### Integrity Checks (`integrity.clj`)

- `(check-null-violations schema data-fn)` — For each non-nullable column, calls `(data-fn table-name column-name)` which returns a count of null values. Returns a sequence of `{:table "t" :column "c" :null-count n}` for columns with null-count > 0
- `(check-foreign-key-orphans schema data-fn)` — For each foreign-key column, calls `(data-fn source-table source-column target-table target-column)` which returns a count of orphaned rows. Returns `{:source-table "t" :source-column "c" :target-table "t2" :orphan-count n}`
- `(check-unique-violations schema data-fn)` — For each unique column, calls `(data-fn table-name column-name)` which returns a count of duplicate values. Returns `{:table "t" :column "c" :duplicate-count n}`
- All functions accept a `data-fn` callback instead of direct DB access for testability

### Report Generation (`report.clj`)

- `(generate-edn-report diff integrity-results)` — Returns an EDN map: `{:timestamp <ISO-8601> :schema-changes diff :integrity-violations integrity-results :severity (calculate-severity diff integrity-results)}`
- `(generate-markdown-report diff integrity-results)` — Returns a Markdown string with headings for Schema Changes, Integrity Violations, and an overall severity rating
- Severity calculation: `:critical` if any non-nullable changes or foreign key orphans; `:warning` if any type changes or unique violations; `:info` if only additions

### Validation Orchestrator (`core.clj`)

- `(validate-migration before-schema after-schema data-fn)` — Orchestrates the full validation: computes diff, runs integrity checks against `after-schema`, generates both EDN and Markdown reports, returns `{:diff diff :integrity checks :edn-report edn :markdown-report md}`
- Must use `->` or `->>` threading macros for pipeline clarity
- Must handle empty schemas gracefully (empty maps produce empty diffs, no errors)

### Expected Functionality

- Comparing a schema with an added `"preferences"` table returns it in `:added-tables`
- Comparing before/after where `"users"."email"` changed from `:nullable true` to `:nullable false` returns it in `:nullable-changes` and triggers `:critical` severity
- Integrity check with a `data-fn` returning 5 null values for a non-nullable column returns `{:null-count 5}`
- Markdown report contains `## Schema Changes`, `## Integrity Violations`, and `## Severity: critical`

## Acceptance Criteria

- All four namespaces compile without errors when loaded
- `compare-schemas` correctly identifies added/removed/modified tables and columns
- Nullable-to-non-nullable changes are flagged as breaking
- Integrity check functions accept `data-fn` callbacks and produce correct violation reports
- Report generation produces valid EDN and well-formatted Markdown
- All functions are pure (no side effects, no global state mutation)
- Tests in `core_test.clj` pass: `clojure -X:test :dirs '["test"]' :patterns '["metabase.migration-validator"]'`
- `python -m pytest /workspace/tests/test_clojure_write.py -v --tb=short` passes
