# Task: Implement a Query Result Cache Namespace in Metabase

## Background

Metabase's Clojure backend needs a new in-memory query result caching namespace that stores recently executed query results with TTL-based expiration, LRU eviction, and size-bounded storage. This cache sits between the API layer and the query processor, keyed by a normalized query hash. The implementation goes into the `src/metabase/` source tree and must include a corresponding test namespace under `test/metabase/`.

## Files to Create/Modify

- `src/metabase/query_result_cache.clj` (create) — Namespace implementing the cache with TTL expiration, LRU eviction, and size bounds
- `test/metabase/query_result_cache_test.clj` (create) — Tests covering all cache operations, TTL behavior, eviction, and edge cases
- `src/metabase/api/dataset.clj` (modify) — Integrate cache lookup/store around query execution in the dataset API endpoint

## Requirements

### Namespace Structure (metabase.query-result-cache)

- Declare namespace `metabase.query-result-cache` with appropriate `:require` clauses
- Use an `atom` holding a map as the primary cache store
- Each cache entry must track: `:result` (the cached value), `:created-at` (epoch millis), `:last-accessed` (epoch millis), `:size-bytes` (estimated size of the result)

### Cache Operations

- `(cache-key query)` — accepts a query map, normalizes it (sorted keys, remove non-deterministic fields like `:middleware` and `:info`), and returns a SHA-256 hex string
- `(cache-get cache-atom key)` — returns the cached result if present and not expired; updates `:last-accessed` timestamp; returns `nil` if missing or expired
- `(cache-put! cache-atom key result max-entries max-total-bytes ttl-ms)` — stores the result, evicting the least-recently-accessed entries first if either `max-entries` or `max-total-bytes` would be exceeded after insertion
- `(cache-invalidate! cache-atom key)` — removes a specific entry
- `(cache-clear! cache-atom)` — removes all entries
- `(cache-stats cache-atom)` — returns a map with `:entry-count`, `:total-bytes`, `:hit-count`, `:miss-count`
- The namespace must maintain `:hit-count` and `:miss-count` counters in a separate atom

### TTL and Eviction

- `cache-get` must check `(- (System/currentTimeMillis) (:created-at entry))` against the configured TTL; if expired, remove the entry and return `nil`
- When `cache-put!` would cause `entry-count > max-entries`, evict the entry with the oldest `:last-accessed` timestamp
- When `cache-put!` would cause total bytes to exceed `max-total-bytes`, evict entries by oldest `:last-accessed` until there is room, or reject the insert if the single entry exceeds `max-total-bytes`
- Eviction must be performed inside a `swap!` to ensure atomicity

### Normalization and Hashing

- `cache-key` must produce identical hashes for query maps that differ only in key ordering
- `cache-key` must strip the following keys before hashing: `:middleware`, `:info`, `:constraints`, `:async?`
- Two queries that differ only in a stripped key must produce the same cache key
- Two queries that differ in `:database` or `:query` (the actual MBQL) must produce different cache keys

### Integration (api/dataset.clj)

- Before executing a query in the `POST /api/dataset` handler, compute the cache key and attempt `cache-get`
- On cache hit, return the cached result directly without running the query
- On cache miss, execute the query, then call `cache-put!` with the result before returning
- Use a default TTL of 300000 ms (5 minutes), max-entries of 1000, max-total-bytes of 52428800 (50 MB)

### Expected Functionality

- `(cache-key {:database 1 :query {:source-table 5}})` and `(cache-key {:query {:source-table 5} :database 1})` → return the same hash string
- `(cache-key {:database 1 :query {:source-table 5} :middleware {:js-int-to-string? true}})` → returns the same hash as above (`:middleware` stripped)
- `(cache-key {:database 1 :query {:source-table 5}})` vs `(cache-key {:database 2 :query {:source-table 5}})` → different hashes
- `(cache-put! c "k1" {:rows [[1]]} 10 1000 5000)` then `(cache-get c "k1")` within 5 seconds → returns `{:rows [[1]]}`
- `(cache-put! c "k1" {:rows [[1]]} 10 1000 5000)` then wait 6 seconds then `(cache-get c "k1")` → returns `nil` (expired)
- Insert 3 entries into a cache with `max-entries` of 2 → the least-recently-accessed of the first two is evicted
- Insert a 100-byte entry into a cache with `max-total-bytes` of 50 → insert is rejected, cache unchanged
- `(cache-stats c)` after 3 hits and 1 miss → `{:entry-count N :total-bytes M :hit-count 3 :miss-count 1}`
- `(cache-invalidate! c "k1")` then `(cache-get c "k1")` → `nil`
- `(cache-clear! c)` then `(cache-stats c)` → `{:entry-count 0 :total-bytes 0 :hit-count 0 :miss-count 0}`

## Acceptance Criteria

- `src/metabase/query_result_cache.clj` loads without errors when evaluated with `clojure.core/require`
- All functions in the namespace are properly defined and callable
- `test/metabase/query_result_cache_test.clj` passes all tests via `clojure -X:test` targeting the namespace
- Cache key normalization produces identical hashes for key-order-permuted maps and correctly strips non-deterministic keys
- TTL expiration removes stale entries and increments the miss counter
- LRU eviction removes the least-recently-accessed entry when max-entries is exceeded
- Size-based eviction removes entries when max-total-bytes would be exceeded, and rejects entries that individually exceed the limit
- Hit/miss counters are accurate across all get operations
- The `POST /api/dataset` endpoint returns cached results on repeated identical queries within the TTL window
- End all source files with a newline character
- No parentheses mismatches — all forms are properly balanced
