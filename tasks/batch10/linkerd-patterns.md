# Task: Implement Service Mesh Policy Engine with ServiceProfile, TrafficSplit, and Authorization Resources

## Background

The Linkerd2 service mesh (`linkerd/linkerd2`) requires a new policy engine in the controller package that validates, processes, and applies ServiceProfile, TrafficSplit, and ServerAuthorization resources. The controller currently manages proxy injection and identity but lacks a unified policy reconciliation layer that enforces per-route retry budgets, weighted traffic splits, and mTLS-based authorization rules. The implementation must live within the existing `controller/` and `pkg/` directory structure.

## Files to Create/Modify

- `controller/policy/engine.go` — Policy engine that reconciles ServiceProfile, TrafficSplit, and ServerAuthorization resources (new)
- `controller/policy/engine_test.go` — Unit tests for the policy engine (new)
- `pkg/profiles/spec.go` — ServiceProfile spec types with route matching, retry budgets, and timeout configuration (new)
- `pkg/profiles/spec_test.go` — Unit tests for ServiceProfile validation and route matching (new)
- `pkg/split/traffic_split.go` — TrafficSplit resource types with weight normalization and backend validation (new)
- `pkg/split/traffic_split_test.go` — Unit tests for TrafficSplit logic (new)
- `pkg/auth/server_authorization.go` — ServerAuthorization types with mTLS identity matching and network CIDR validation (new)
- `pkg/auth/server_authorization_test.go` — Unit tests for authorization evaluation (new)

## Requirements

### ServiceProfile Resource

- Define `ServiceProfile` struct with `Name`, `Namespace`, `FQDN string` (format: `<service>.<namespace>.svc.cluster.local`), `Routes []RouteSpec`, `RetryBudget RetryBudgetSpec`
- Each `RouteSpec` contains: `Name string`, `Method string`, `PathRegex string`, `IsRetryable bool`, `Timeout time.Duration`, `ResponseClasses []ResponseClassSpec`
- `ResponseClassSpec` has `StatusMin int`, `StatusMax int`, `IsFailure bool`
- `RetryBudgetSpec` has `RetryRatio float64`, `MinRetriesPerSecond int`, `TTL time.Duration`
- `Validate()` must reject: empty FQDN, FQDN not matching the `<svc>.<ns>.svc.cluster.local` pattern, `RetryRatio` outside (0.0, 1.0], `MinRetriesPerSecond` < 0, invalid regex in `PathRegex`, `StatusMin` > `StatusMax`, `StatusMin` < 100 or `StatusMax` > 599
- `MatchRoute(method string, path string)` returns the first matching `RouteSpec` or nil if no route matches

### TrafficSplit Resource

- Define `TrafficSplit` struct with `Name`, `Namespace`, `ServiceName string` (the apex service), `Backends []TrafficBackend`
- Each `TrafficBackend` has `Service string`, `Weight int` (milliunits, 0–1000)
- `Validate()` must reject: zero backends, total weight not summing to 1000, any backend with weight < 0 or > 1000, duplicate backend service names, apex `ServiceName` appearing as a backend
- `NormalizeWeights()` adjusts weights proportionally so they sum to exactly 1000 when input weights don't sum correctly, rounding the remainder onto the largest-weight backend
- `GetBackendForValue(v int)` takes a value 0–999 and returns the backend via weighted selection (first backend covers [0, weight1), second covers [weight1, weight1+weight2), etc.)

### ServerAuthorization Resource

- Define `Server` struct with `Name`, `Namespace`, `PodSelector map[string]string`, `Port string`, `ProxyProtocol string` (one of `HTTP/1`, `HTTP/2`, `gRPC`, `opaque`)
- Define `ServerAuthorization` struct with `Name`, `Namespace`, `ServerName string`, `MeshTLSIdentities []Identity`, `UnauthenticatedAccess bool`, `Networks []string` (CIDR notation)
- `Identity` has `ServiceAccount string`, `Namespace string`
- `Validate()` must reject: empty `ServerName`, invalid CIDR strings in `Networks`, `UnauthenticatedAccess: true` combined with non-empty `MeshTLSIdentities` (mutually exclusive), empty `PodSelector` on `Server`, `ProxyProtocol` not in the allowed set
- `Evaluate(sourceIdentity Identity, sourceIP string)` returns `Allow` or `Deny` — allows if source identity matches any `MeshTLSIdentities`, or if `UnauthenticatedAccess` is true and source IP falls within any `Networks` CIDR

### Policy Engine

- `PolicyEngine` struct holds maps of ServiceProfiles, TrafficSplits, and ServerAuthorizations keyed by `namespace/name`
- `Apply(resource interface{})` validates and stores the resource; returns error if validation fails
- `Remove(kind string, namespace string, name string)` deletes a resource from the engine
- `EvaluateRequest(namespace, service, method, path string, sourceIdentity Identity, sourceIP string)` performs authorization check then returns the matched route's timeout and retry configuration along with the traffic split decision for the service
- If no ServerAuthorization exists for the service's server, default policy is `Deny`
- If no ServiceProfile exists, return nil route (no timeout/retry config)
- If no TrafficSplit exists, return the original service as the sole backend

### Expected Functionality

- ServiceProfile with FQDN `orders.default.svc.cluster.local`, route `GET /api/orders/[^/]+` → `MatchRoute("GET", "/api/orders/123")` returns that route
- ServiceProfile with FQDN `orders.default.svc.cluster.local` → `MatchRoute("POST", "/api/unknown")` returns nil
- TrafficSplit with backends `[{stable, 900}, {canary, 100}]` → `GetBackendForValue(850)` returns `stable`, `GetBackendForValue(950)` returns `canary`
- TrafficSplit with weights `[600, 300]` (sum 900) → `NormalizeWeights()` adjusts to `[667, 333]` (sum 1000)
- ServerAuthorization with identity `{frontend, default}` → `Evaluate({frontend, default}, "10.0.0.1")` returns `Allow`
- ServerAuthorization with identity `{frontend, default}` → `Evaluate({backend, default}, "10.0.0.1")` returns `Deny`
- ServerAuthorization with `UnauthenticatedAccess: true`, networks `["10.0.0.0/8"]` → `Evaluate({}, "10.0.0.5")` returns `Allow`; `Evaluate({}, "192.168.0.1")` returns `Deny`
- PolicyEngine with no authorization for service → `EvaluateRequest()` returns `Deny`
- CIDR validation: network `"not-a-cidr"` → `Validate()` returns error containing "invalid CIDR"

## Acceptance Criteria

- `go test ./controller/policy/ -v` passes all tests
- `go test ./pkg/profiles/ -v` passes all tests
- `go test ./pkg/split/ -v` passes all tests
- `go test ./pkg/auth/ -v` passes all tests
- ServiceProfile validates FQDN format, regex patterns, status code ranges, and retry budget bounds
- TrafficSplit rejects invalid weight configurations and correctly normalizes unbalanced weights
- ServerAuthorization enforces mutual exclusivity between mTLS identities and unauthenticated access
- CIDR-based network matching correctly handles IPv4 ranges and rejects malformed CIDR strings
- PolicyEngine default-deny behavior is enforced when no authorization rule matches
- Route matching uses regex evaluation, not string equality
- No hardcoded IP addresses or identities in test assertions
