# Task: Implement Linkerd Service Mesh Traffic Management and Authorization Policies

## Background

Linkerd (https://github.com/linkerd/linkerd2) is a lightweight Kubernetes service mesh. A new Go package is needed that generates Linkerd-specific custom resources for a microservices application: ServiceProfiles (per-route metrics, retries, timeouts), TrafficSplit resources (canary deployments with weighted routing), Server/ServerAuthorization policies (zero-trust network access), and a canary promotion controller that evaluates success rate metrics to advance or roll back traffic splits.

## Files to Create/Modify

- `pkg/linkerd/serviceprofile.go` (create) — `ServiceProfileGenerator` that creates Linkerd `ServiceProfile` resources from OpenAPI specs, defining routes with per-route retry budgets, timeouts, and response classes
- `pkg/linkerd/trafficsplit.go` (create) — `TrafficSplitManager` that generates and manages SMI `TrafficSplit` resources for canary deployments with configurable weight increments
- `pkg/linkerd/authorization.go` (create) — `AuthorizationPolicyGenerator` that creates `Server`, `ServerAuthorization`, and `AuthorizationPolicy` resources for zero-trust access control between services
- `pkg/linkerd/canary.go` (create) — `CanaryController` that evaluates Prometheus success-rate metrics against thresholds and advances/rolls back traffic splits
- `pkg/linkerd/types.go` (create) — Shared types: `ServiceConfig`, `CanaryConfig`, `AuthzConfig`, `Route`, `TrafficWeight`
- `pkg/linkerd/linkerd_test.go` (create) — Unit tests for all generators and the canary controller logic

## Requirements

### Types (`types.go`)

- `ServiceConfig` struct: `Name string`, `Namespace string`, `Port int`, `Protocol string` (HTTP or gRPC), `Routes []Route`
- `Route` struct: `Name string`, `Method string`, `PathRegex string`, `IsRetryable bool`, `TimeoutMs int`
- `CanaryConfig` struct: `Service string`, `CanaryService string`, `StepWeight int` (percentage increment per step), `MaxWeight int`, `SuccessRateThreshold float64` (e.g., 0.99), `Interval time.Duration`
- `AuthzConfig` struct: `ServerName string`, `Port int`, `AllowedClients []string` (service account names), `AllowedNamespaces []string`, `UnauthenticatedAllowed bool`
- `TrafficWeight` struct: `Service string`, `Weight int`

### ServiceProfile Generator (`serviceprofile.go`)

- Function `GenerateServiceProfile(config ServiceConfig) (*ServiceProfileManifest, error)`
- Output is a Linkerd `ServiceProfile` CR:
  - `apiVersion: linkerd.io/v1alpha2`
  - `kind: ServiceProfile`
  - `metadata.name: <service>.<namespace>.svc.cluster.local`
  - `spec.routes[]` — one entry per route in config:
    - `name`: route name
    - `condition.method`: HTTP method
    - `condition.pathRegex`: path regex
    - `isRetryable`: from config
    - `timeout`: formatted as Go duration string (e.g., `500ms`)
  - `spec.retryBudget.retryRatio: 0.2`, `retryBudget.minRetriesPerSecond: 10`, `retryBudget.ttl: 10s`
- For gRPC protocol, set `condition.method: POST` and `condition.pathRegex: /package\.Service/Method`
- Validate: at least one route required, timeout must be positive, pathRegex must compile

### TrafficSplit Manager (`trafficsplit.go`)

- Function `GenerateTrafficSplit(primary, canary string, namespace string, weights []TrafficWeight) (*TrafficSplitManifest, error)`
- Output is an SMI `TrafficSplit` CR:
  - `apiVersion: split.smi-spec.io/v1alpha2`
  - `kind: TrafficSplit`
  - `metadata.name: <primary>-split`
  - `spec.service: <primary>`
  - `spec.backends[]` — one entry per weight with `service` and `weight` fields
- Weights must sum to 100; return error if they don't
- Function `AdvanceCanary(current TrafficSplitManifest, step int) (*TrafficSplitManifest, error)` — Shift `step` percentage points from primary to canary (e.g., 90/10 → 80/20)
- Function `RollbackCanary(split TrafficSplitManifest) (*TrafficSplitManifest, error)` — Set primary to 100%, canary to 0%

### Authorization Policy Generator (`authorization.go`)

- Function `GenerateAuthorizationPolicies(config AuthzConfig) ([]Manifest, error)` — Returns 2 or 3 resources:
  1. `Server` resource (`policy.linkerd.io/v1beta1`):
     - `spec.podSelector.matchLabels: {app: <config.ServerName>}`
     - `spec.port: <config.Port>`
     - `spec.proxyProtocol: HTTP/2` for gRPC or `HTTP/1` for HTTP
  2. `ServerAuthorization` resource (`policy.linkerd.io/v1beta1`):
     - `spec.server.name: <server-name>`
     - `spec.client.meshTLS.serviceAccounts[]` — entries for each allowed client
     - If `UnauthenticatedAllowed` is true, add `spec.client.unauthenticated: true` instead
  3. `AuthorizationPolicy` resource (if namespace restrictions apply):
     - `spec.targetRef` pointing to the Server
     - `spec.requiredAuthenticationRefs` for mTLS identity
- If `AllowedClients` is empty and `UnauthenticatedAllowed` is false, return error "no access policy defined"

### Canary Controller (`canary.go`)

- Struct `CanaryController` with field `MetricsFetcher func(service string) (float64, error)` (returns success rate)
- Method `Evaluate(config CanaryConfig, current TrafficSplitManifest) (Action, *TrafficSplitManifest, error)`:
  - `Action` is enum: `ADVANCE`, `ROLLBACK`, `COMPLETE`
  - Fetch success rate for the canary service
  - If success rate >= threshold and canary weight < max weight: return `ADVANCE` with advanced split
  - If success rate >= threshold and canary weight >= max weight: return `COMPLETE` (canary becomes primary)
  - If success rate < threshold: return `ROLLBACK` with rollback split
- Method `RunLoop(ctx context.Context, config CanaryConfig, initial TrafficSplitManifest) ([]Action, error)` — Evaluates repeatedly at `config.Interval` until COMPLETE or ROLLBACK, returns action history

### Expected Functionality

- ServiceProfile for an HTTP service with routes GET `/api/users` and POST `/api/users` produces 2 route entries with correct conditions
- TrafficSplit starting at 100/0 advancing by step=10 produces 90/10 after first advance
- Authorization policy for service "api" allowing clients ["web", "worker"] generates Server + ServerAuthorization with 2 service account entries
- Canary controller with success rate 0.995 (above 0.99 threshold) returns ADVANCE action

## Acceptance Criteria

- ServiceProfile YAML contains correct apiVersion, route conditions, retry budgets, and timeouts
- TrafficSplit weights always sum to 100; advance and rollback produce correct weight distributions
- Authorization policies enforce zero-trust: no client access unless explicitly allowed
- Canary controller correctly evaluates success rate against threshold for advance/rollback decisions
- All generated YAML is valid and parseable
- `python -m pytest /workspace/tests/test_linkerd_patterns.py -v --tb=short` passes
