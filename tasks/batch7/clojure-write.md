# Task: Implement a Query Result Digest Notification Service in Metabase

## Background

Metabase (https://github.com/metabase/metabase) is an open-source analytics platform. Users frequently need to be notified when query results change beyond a specified threshold. The task is to implement a Clojure namespace that monitors saved questions (cards), computes digests of their results, detects changes, and produces notification payloads — integrated into Metabase's existing query processor and Toucan model infrastructure.

## Files to Create/Modify

- `src/metabase/query_processor/middleware/result_digest.clj` (create) — Middleware that computes a SHA-256 digest of query results for change detection
- `src/metabase/notification/result_change.clj` (create) — Service that compares current result digests against stored digests and produces notification payloads when changes exceed the configured threshold
- `test/metabase/query_processor/middleware/result_digest_test.clj` (create) — Tests for the digest computation middleware
- `test/metabase/notification/result_change_test.clj` (create) — Tests for the change detection and notification service

## Requirements

### Result Digest Middleware (`result_digest.clj`)

- Namespace: `metabase.query-processor.middleware.result-digest`
- Implement a function `compute-digest` that takes a query result map (with `:rows` and `:cols` keys) and returns a hex-encoded SHA-256 digest string
  - Serialize the result `:rows` (vector of vectors) to a canonical string representation using `pr-str`
  - Include the column names (from `:cols`) in the digest to detect schema changes
  - Return a map `{:digest <hex-string> :row-count <int> :col-count <int>}`
- Implement `result-digest-middleware` as a query processor middleware function following Metabase's middleware conventions:
  - Accepts `[query rff]` arguments
  - Wraps the `rff` (reducing function function) to intercept the final result
  - Attaches the computed digest under the key `:result-digest` in the query result metadata
  - Passes through to the next middleware if digest computation is not requested (check for `:compute-digest? true` in the query map)

### Change Detection Service (`result_change.clj`)

- Namespace: `metabase.notification.result-change`
- Implement `check-card-for-changes` that accepts a card ID and:
  1. Loads the card from the database using `(t2/select-one :model/Card :id card-id)`
  2. Executes the card's query with digest computation enabled
  3. Retrieves the previously stored digest from the `result_digest_cache` table (if it exists)
  4. Compares the new digest with the stored digest
  5. Returns `nil` if the digests match, or a notification payload map if they differ

- Notification payload structure:
  ```clojure
  {:card-id       <int>
   :card-name     <string>
   :change-type   <:new-results | :schema-change | :row-count-change | :data-change>
   :previous      {:digest <string> :row-count <int> :col-count <int>}
   :current       {:digest <string> :row-count <int> :col-count <int>}
   :detected-at   <java.time.Instant>}
  ```

- Determine `:change-type` as follows:
  - `:new-results` if no previous digest exists
  - `:schema-change` if `col-count` differs between previous and current
  - `:row-count-change` if `row-count` differs but `col-count` is the same
  - `:data-change` if both counts are the same but the digest differs

- Implement `check-all-monitored-cards` that:
  1. Queries all cards where `:result_digest_monitoring` is `true`
  2. Calls `check-card-for-changes` for each
  3. Filters out `nil` results
  4. Returns a sequence of notification payloads

- Implement `update-stored-digest` that saves the current digest to the `result_digest_cache` table for a given card ID (upsert: insert or update if exists)

### Data Model

- The `result_digest_cache` table has columns: `card_id` (integer, primary key), `digest` (varchar 64), `row_count` (integer), `col_count` (integer), `computed_at` (timestamp)
- Access this table via Toucan 2 (`t2/select-one`, `t2/insert!`, `t2/update!`)

### Constraints

- All functions must be pure where possible (side effects only in `check-card-for-changes`, `update-stored-digest`, and `check-all-monitored-cards`)
- Use `metabase.util.log` for logging (not `println` or `clojure.tools.logging` directly)
- Use `java.security.MessageDigest` for SHA-256 computation
- Handle missing cards gracefully: if a card with the given ID doesn't exist, return `nil` from `check-card-for-changes`
- Handle query execution errors: if the query fails, log the error and return `nil` (do not propagate the exception)

## Expected Functionality

- `(compute-digest {:rows [[1 "a"] [2 "b"]] :cols [{:name "id"} {:name "val"}]})` returns a map with `:digest` (64-char hex string), `:row-count 2`, `:col-count 2`
- Two identical result sets produce the same digest; changing any cell value produces a different digest
- Adding a column to the result (schema change) produces a `:schema-change` notification
- Adding rows without changing schema produces a `:row-count-change` notification
- Changing cell values without changing row/column counts produces a `:data-change` notification
- First-time check on a card with no stored digest produces a `:new-results` notification

## Acceptance Criteria

- `compute-digest` produces deterministic SHA-256 hex digests for identical inputs
- `compute-digest` produces different digests when rows, column names, or cell values differ
- `result-digest-middleware` attaches `:result-digest` metadata only when `:compute-digest?` is `true` in the query
- `check-card-for-changes` returns the correct `:change-type` for each of the four scenarios
- `check-card-for-changes` returns `nil` for nonexistent card IDs and for cards whose results have not changed
- `update-stored-digest` performs an upsert (insert on first call, update on subsequent calls for the same card)
- All functions handle edge cases: empty result sets, single-row results, results with zero columns
