# Task: Implement VirtualService and DestinationRule Traffic Management for Istio

## Background

Istio (https://github.com/istio/istio) is a service mesh that provides traffic management, security, and observability for microservices. The project needs traffic management configuration generators in the `pilot/` package that create VirtualService and DestinationRule resources for canary deployments, circuit breaking, fault injection, and retry policies.

## Files to Create/Modify

- `pilot/pkg/config/traffic/virtualservice_builder.go` (create) — VirtualService configuration builder with routing rules, fault injection, and retries
- `pilot/pkg/config/traffic/destinationrule_builder.go` (create) — DestinationRule builder with circuit breaker, load balancing, and connection pool configuration
- `pilot/pkg/config/traffic/canary.go` (create) — Canary deployment configuration combining VirtualService and DestinationRule
- `pilot/pkg/config/traffic/virtualservice_builder_test.go` (create) — Tests for VirtualService builder
- `pilot/pkg/config/traffic/destinationrule_builder_test.go` (create) — Tests for DestinationRule builder

## Requirements

### VirtualService Builder

- Implement a `VirtualServiceBuilder` that constructs Istio `VirtualService` resources:
  - `hosts` (list of strings, required, at least one)
  - `gateways` (optional, list of gateway references)
  - HTTP route rules with: `match` conditions (URI prefix/exact/regex, headers, query params), `route` destinations with `host`, `subset`, and `weight` (percentage, 0–100)
  - Route weights across all destinations in a rule must sum to 100; return error if not
- Support fault injection:
  - `delay` — inject a fixed delay (duration) for a percentage of requests
  - `abort` — return a specific HTTP status code for a percentage of requests
  - Fault percentage must be 0.0–100.0; return error if out of range
- Support retry policy: `attempts` (int), `perTryTimeout` (duration), `retryOn` (comma-separated conditions like `"5xx,connect-failure,retriable-4xx"`)
- Support request timeout: overall timeout for the entire request including retries
- Generate YAML with `apiVersion: networking.istio.io/v1beta1` and `kind: VirtualService`

### DestinationRule Builder

- Implement a `DestinationRuleBuilder` that constructs Istio `DestinationRule` resources:
  - `host` (string, required — the service hostname)
  - `subsets` — list of named subsets with label selectors (e.g., `{name: "v1", labels: {"version": "v1"}}`)
  - Traffic policy with:
    - **Connection pool**: `maxConnections` (TCP), `http1MaxPendingRequests`, `http2MaxRequests`
    - **Circuit breaker (outlier detection)**: `consecutive5xxErrors` (threshold, default 5), `interval` (check interval, default `10s`), `baseEjectionTime` (default `30s`), `maxEjectionPercent` (0–100, default 100)
    - **Load balancing**: `simple` mode (one of `ROUND_ROBIN`, `LEAST_REQUEST`, `RANDOM`, `PASSTHROUGH`)
- Validate: `maxEjectionPercent` must be 0–100; invalid load balancing mode returns error
- Generate YAML with `apiVersion: networking.istio.io/v1beta1` and `kind: DestinationRule`

### Canary Deployment Configuration

- Implement a `CanaryConfig` that generates both VirtualService and DestinationRule for a canary deployment:
  - Input: service name, stable version label, canary version label, canary weight percentage (0–100)
  - Generate VirtualService with two weighted routes: stable gets `(100 - canary_weight)%`, canary gets `canary_weight%`
  - Generate DestinationRule with two subsets: `stable` (matching stable version label) and `canary` (matching canary version label)
  - Support `progressive_rollout(steps []int)` — generates a series of configurations with increasing canary weights (e.g., [5, 25, 50, 100])
  - Each step in progressive rollout must be > previous step; return error if not monotonically increasing
  - The final step (100%) should also update the stable subset to point to the canary version

### Expected Functionality

- A VirtualService with routes 80% to v1 and 20% to v2 produces correct YAML with weight annotations
- Routes with weights [60, 30] (sum=90) return an error
- A fault injection with delay=5s for 10% of requests to `/api/orders` produces correct YAML output
- A DestinationRule with outlier detection ejecting after 3 consecutive 5xx errors produces correct circuit breaker config
- Load balancing mode `"INVALID"` returns an error
- Canary config for `reviews` service with 10% canary weight produces VirtualService (90/10 split) and DestinationRule (stable/canary subsets)
- Progressive rollout [5, 25, 50, 100] generates 4 configuration pairs
- Progressive rollout [50, 25, 75] returns error (not monotonically increasing)

## Acceptance Criteria

- VirtualService YAML includes correct route weights, match conditions, fault injection, retry policy, and timeouts
- Route weights summing to != 100 are rejected with error
- Fault injection percentage is validated in range 0.0–100.0
- DestinationRule YAML includes correct subsets, connection pool, outlier detection, and load balancing configuration
- Circuit breaker `maxEjectionPercent` validation rejects values outside 0–100
- Canary configuration generates matching VirtualService and DestinationRule pairs
- Progressive rollout validates monotonically increasing weights and generates correct configuration series
- All generated YAML uses correct Istio apiVersion and kind
- Tests cover valid configurations, weight validation, fault injection, circuit breaker settings, and progressive rollout
