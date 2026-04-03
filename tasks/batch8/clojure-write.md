# Task: Implement a Data Catalog Namespace for Metabase's Internal Metadata Registry

## Background

Metabase's backend is written in Clojure and uses a namespace-based architecture for organizing functionality. A new namespace is needed to provide a data catalog feature — an internal registry that tracks metadata about databases, tables, and fields across connected data sources. The catalog aggregates metadata from Metabase's existing models and exposes functions for querying, searching, and reporting on the available data assets.

## Files to Create/Modify

- `src/metabase/catalog/core.clj` (new) — Core namespace with public API functions for querying the data catalog (list databases, search tables, get field lineage)
- `src/metabase/catalog/registry.clj` (new) — Internal registry that aggregates metadata from Metabase database, table, and field models into a unified catalog structure
- `src/metabase/catalog/search.clj` (new) — Search functions supporting full-text matching across table names, descriptions, and field names with relevance ranking
- `src/metabase/catalog/stats.clj` (new) — Statistics aggregation functions computing per-database and per-table metrics (row count estimates, field count, query frequency)
- `test/metabase/catalog/core_test.clj` (new) — Tests for the catalog public API
- `test/metabase/catalog/search_test.clj` (new) — Tests for the search functionality

## Requirements

### Catalog Registry

- `(registry/build-catalog)` scans all active databases in Metabase and returns a map keyed by database ID, where each entry contains `:name`, `:engine`, `:tables` (a vector of table metadata maps)
- Each table metadata map contains: `:id`, `:name`, `:schema`, `:description`, `:field_count`, `:fields` (vector of field maps with `:id`, `:name`, `:base_type`, `:semantic_type`, `:description`)
- Databases with `is_audit` set to true must be excluded from the catalog
- Tables with `visibility_type` set to `"hidden"` or `"technical"` must be excluded
- The catalog must be buildable incrementally: `(registry/update-catalog catalog db-id)` refreshes only the specified database's entry

### Search Functions

- `(search/find-tables catalog query-string)` returns a ranked list of tables whose `:name` or `:description` contains the query string (case-insensitive substring match)
- `(search/find-fields catalog query-string)` returns a ranked list of `{:database_name :table_name :field_name :base_type}` maps for fields matching the query
- Results are ranked by: exact name match first, then prefix match, then substring match
- If `query-string` is blank or nil, return an empty vector
- Maximum 50 results per search call; results beyond 50 are truncated

### Statistics Functions

- `(stats/database-summary catalog db-id)` returns `{:database_name :table_count :total_field_count :avg_fields_per_table}`
- `(stats/table-detail catalog db-id table-id)` returns `{:table_name :schema :field_count :fields_by_type}` where `:fields_by_type` is a frequency map of `:base_type` values (e.g., `{"type/Integer" 5, "type/Text" 3}`)
- If the database or table ID is not found in the catalog, return `nil`

### Public API (core namespace)

- `(core/get-catalog)` returns the full catalog (calls `registry/build-catalog`)
- `(core/search query-string)` delegates to `search/find-tables` and `search/find-fields`, returning `{:tables [...] :fields [...]}`
- `(core/database-stats db-id)` delegates to `stats/database-summary`
- `(core/refresh-database db-id)` delegates to `registry/update-catalog`
- All public functions must return plain Clojure data structures (maps and vectors), not Java objects or database result sets

### Expected Functionality

- Building a catalog with 2 active databases (one with 10 tables, one with 5 tables) and 1 audit database → catalog contains 2 entries, audit database excluded
- A database with 3 tables where 1 has `visibility_type: "hidden"` → catalog entry for that database contains 2 tables
- `(search/find-tables catalog "user")` against tables named "users", "user_accounts", "orders", "product_users" → returns "users" first (exact prefix), then "user_accounts", then "product_users"
- `(search/find-fields catalog "email")` returns field entries matching "email" across all databases and tables
- `(search/find-tables catalog "")` returns empty vector
- `(stats/database-summary catalog 1)` for a database with 10 tables and 80 total fields → `{:table_count 10, :total_field_count 80, :avg_fields_per_table 8.0}`
- `(stats/database-summary catalog 999)` for a nonexistent database → `nil`

## Acceptance Criteria

- The catalog registry correctly aggregates metadata from all active, non-audit databases and excludes hidden/technical tables
- Incremental catalog updates via `update-catalog` refresh only the targeted database without affecting other entries
- Search functions return correctly ranked results with exact/prefix matches prioritized over substring matches
- Search with blank or nil input returns an empty vector; results are capped at 50
- Statistics functions compute accurate counts and type frequency maps
- All public API functions return plain Clojure data structures
- Tests verify catalog building, filtering (audit databases, hidden tables), search ranking, statistics computation, and nil/empty edge cases
