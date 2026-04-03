# Task: Add Retry Budget and Request Timeout Policy Support to Linkerd's Destination Controller

## Background

Linkerd (https://github.com/linkerd/linkerd2) is a lightweight service mesh for Kubernetes. The destination controller resolves service endpoints and provides traffic policy configuration to the data plane proxies. The task is to add support for per-route retry budgets and request timeout policies that are configured via `ServiceProfile` resources and served to proxies through the destination API.

## Files to Create/Modify

- `controller/api/destination/retry_budget.go` (create) — `RetryBudgetCalculator` that computes per-service retry budgets based on request rates and configurable parameters
- `controller/api/destination/timeout_policy.go` (create) — `TimeoutPolicyResolver` that resolves per-route timeout configurations from `ServiceProfile` specs
- `controller/api/destination/watcher/profile_watcher.go` (modify) — Extend the profile watcher to parse and propagate retry budget and timeout policy from `ServiceProfile` resources
- `controller/api/destination/retry_budget_test.go` (create) — Unit tests for retry budget calculation
- `controller/api/destination/timeout_policy_test.go` (create) — Unit tests for timeout policy resolution

## Requirements

### `RetryBudgetCalculator` (`retry_budget.go`)

```go
type RetryBudgetConfig struct {
    RetryRatio          float64       // Max fraction of requests that can be retries (e.g., 0.2 = 20%)
    MinRetriesPerSecond uint32        // Minimum retries per second regardless of ratio (e.g., 10)
    TTL                 time.Duration // Time window for rate calculation (e.g., 10s)
}

type RetryBudget struct {
    TotalRequestsInWindow int64
    RetriesInWindow       int64
    AllowRetry            bool
    CurrentRetryRatio     float64
    RemainingBudget       int64
}
```

#### `NewRetryBudgetCalculator(config RetryBudgetConfig) *RetryBudgetCalculator`

#### Methods

- `RecordRequest()` — Records a new outgoing request in the sliding window
- `RecordRetry()` — Records a retry attempt in the sliding window
- `ShouldRetry() RetryBudget`:
  1. Count total requests and retries within the TTL window
  2. Compute current retry ratio: `retries / totalRequests`
  3. Allow retry if either:
     a. `retries < minRetriesPerSecond * TTL.Seconds()` (under minimum floor), OR
     b. `currentRetryRatio < retryRatio` (under the budget ratio)
  4. Return a `RetryBudget` with the current state
- `Reset()` — Clears the sliding window counters

#### Sliding Window Implementation

- Use a ring buffer of per-second buckets to track requests and retries
- Each bucket covers 1 second; the window holds `TTL / 1s` buckets
- On each call, expire buckets older than TTL
- Thread-safe: use `sync.Mutex` for concurrent access

### `TimeoutPolicyResolver` (`timeout_policy.go`)

```go
type TimeoutPolicy struct {
    RequestTimeout    time.Duration // Maximum time for a single request
    IdleTimeout       time.Duration // Maximum idle time on a connection
    StreamTimeout     time.Duration // Maximum time for a streaming RPC
    RetryTimeout      time.Duration // Timeout for each retry attempt (may be shorter than RequestTimeout)
}

type RouteTimeoutConfig struct {
    RouteName string
    Timeout   TimeoutPolicy
}
```

#### `ResolveTimeouts(profile *sp.ServiceProfile) []RouteTimeoutConfig`

1. Iterate over `profile.Spec.Routes`
2. For each route, extract timeout annotations:
   - `config.linkerd.io/request-timeout` → `RequestTimeout`
   - `config.linkerd.io/idle-timeout` → `IdleTimeout`
   - `config.linkerd.io/stream-timeout` → `StreamTimeout`
   - `config.linkerd.io/retry-timeout` → `RetryTimeout`
3. Parse each annotation value as a Go `time.Duration` (e.g., `"500ms"`, `"5s"`, `"1m"`)
4. Apply defaults: if `RequestTimeout` is not set, default to `10s`; if `IdleTimeout` is not set, default to `60s`; `StreamTimeout` and `RetryTimeout` default to `0` (no timeout)
5. Validate: `RetryTimeout` must be ≤ `RequestTimeout` (if both are set); log a warning and clamp if violated
6. Return a list of `RouteTimeoutConfig` entries, one per route

### Profile Watcher Extension (`profile_watcher.go`)

- When a `ServiceProfile` is created or updated, parse the retry budget configuration from the annotation `config.linkerd.io/retry-budget`:
  ```yaml
  metadata:
    annotations:
      config.linkerd.io/retry-budget: '{"retryRatio": 0.2, "minRetriesPerSecond": 10, "ttl": "10s"}'
  ```
- Instantiate a `RetryBudgetCalculator` for each service that has a retry budget annotation
- Call `ResolveTimeouts` to extract per-route timeout policies
- Store both in the profile watcher's cache, keyed by service name
- Expose a method `GetRetryBudget(serviceName string) *RetryBudget` that returns the current budget state
- Expose a method `GetTimeoutPolicies(serviceName string) []RouteTimeoutConfig` that returns resolved timeout configs

## Expected Functionality

- Given a service with retry budget `{retryRatio: 0.2, minRetriesPerSecond: 10, ttl: 10s}`:
  - After 100 requests and 15 retries in the window: `ShouldRetry` returns `AllowRetry: true` (15/100 = 15% < 20%)
  - After 100 requests and 25 retries: `ShouldRetry` returns `AllowRetry: false` (25/100 = 25% > 20%)
  - After 0 requests and 5 retries: `ShouldRetry` returns `AllowRetry: true` (under minRetriesPerSecond floor of 10 * 10 = 100)

- Given a route with `request-timeout: 500ms` and `retry-timeout: 200ms`:
  - `ResolveTimeouts` returns a policy with `RequestTimeout: 500ms` and `RetryTimeout: 200ms`
  - If `retry-timeout: 1s` (exceeds request-timeout), it's clamped to `500ms` with a warning

## Acceptance Criteria

- `RetryBudgetCalculator` uses a sliding window ring buffer that correctly expires old buckets
- `ShouldRetry` allows retries when under either the ratio budget or the minimum floor
- `ShouldRetry` blocks retries when both the ratio is exceeded and retries exceed the minimum floor
- The calculator is thread-safe under concurrent `RecordRequest`/`RecordRetry`/`ShouldRetry` calls
- `TimeoutPolicyResolver` correctly parses duration annotations from `ServiceProfile` routes
- Default timeouts are applied when annotations are missing
- `RetryTimeout > RequestTimeout` is detected and clamped with a warning log
- Profile watcher creates/updates retry budget calculators and timeout policies when profiles change
- All unit tests pass with various request/retry patterns and timeout configurations
