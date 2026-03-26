# Task: Implement Service Profile and Traffic Split Configuration for Linkerd

## Background

Linkerd (https://github.com/linkerd/linkerd2) is a lightweight service mesh for Kubernetes. The project needs enhancement to its service profile and traffic management capabilities in the `controller/` package. This includes route-based metrics, retry budgets, timeout configuration, traffic splitting for canary deployments, and authorization policy generation.

## Files to Create/Modify

- `controller/api/destination/service_profile_builder.go` (create) — Service profile builder with route specifications, retry budgets, and timeouts
- `controller/api/destination/traffic_split.go` (create) — Traffic split configuration for canary deployments with weight validation
- `controller/api/destination/auth_policy.go` (create) — Server authorization policy generator
- `controller/api/destination/service_profile_builder_test.go` (create) — Tests for service profile builder
- `controller/api/destination/traffic_split_test.go` (create) — Tests for traffic split configuration

## Requirements

### Service Profile Builder

- Implement a `ServiceProfileBuilder` that constructs Linkerd `ServiceProfile` custom resources
- Each service profile contains a list of `RouteSpec` entries, each with:
  - `name` (string, required, must be unique within the profile)
  - `condition` — route matching condition with `method` (HTTP method) and `pathRegex` (regex pattern for the path)
  - `isRetryable` (bool) — whether failed requests on this route should be retried
  - `timeout` (duration string, e.g., `"500ms"`, `"2s"`) — per-request timeout for this route
- Configure a `retryBudget` on the profile: `retryRatio` (float, 0.0–1.0, default 0.2), `minRetriesPerSecond` (int, default 10), `ttl` (duration, default `"10s"`)
- Validate: duplicate route names raise an error; `retryRatio` must be 0.0–1.0; timeout must be parseable as a Go duration
- Generate the output as a Kubernetes-style YAML manifest with `apiVersion: linkerd.io/v1alpha2` and `kind: ServiceProfile`

### Traffic Split Configuration

- Implement a `TrafficSplitBuilder` that creates SMI `TrafficSplit` resources for canary deployments
- Accept a `root_service` name and a list of `backends`, each with `service` name and `weight` (int, 0–1000)
- Validate: all weights must sum to 1000 (representing parts per thousand); return error if not
- Validate: at least 2 backends are required (primary and canary); return error if fewer
- Support a `shift_weight(from_backend, to_backend, amount)` method that transfers weight between backends while maintaining the total
- Generate as YAML with `apiVersion: split.smi-spec.io/v1alpha2` and `kind: TrafficSplit`

### Authorization Policy

- Implement an `AuthPolicyBuilder` that generates Linkerd `ServerAuthorization` resources
- Each policy specifies: `server` (reference to a Server resource), `client` (allowed clients by namespace, service account, or both)
- Support three modes:
  - `allow_authenticated` — allow any meshed (mTLS) client
  - `allow_namespaces` — allow clients from specific namespaces only
  - `allow_service_accounts` — allow specific service accounts only
- Generate as YAML with `apiVersion: policy.linkerd.io/v1beta1` and `kind: ServerAuthorization`
- Validate: at least one client specification is required; return error if none provided

### Expected Functionality

- A service profile with routes `GET /users/{id}` and `POST /users` produces correct `pathRegex` and method conditions
- Setting `retryRatio=1.5` raises a validation error (must be ≤ 1.0)
- A traffic split with backends `[{primary, 900}, {canary, 100}]` produces valid YAML with weights summing to 1000
- `shift_weight("primary", "canary", 50)` changes weights to `[{primary, 850}, {canary, 150}]`
- A traffic split with weights `[500, 400]` (sum=900) raises a validation error
- An auth policy allowing namespace `"production"` generates a `ServerAuthorization` with the correct namespace selector
- An auth policy with no client specification raises a validation error

## Acceptance Criteria

- `ServiceProfileBuilder` produces valid Linkerd ServiceProfile YAML with routes, retry budget, and timeouts
- Route name uniqueness and retry ratio range are validated with descriptive errors
- `TrafficSplitBuilder` produces valid SMI TrafficSplit YAML with weights summing to 1000
- `shift_weight` correctly transfers weight between backends while maintaining the total
- Fewer than 2 backends and incorrect weight sums are rejected with errors
- `AuthPolicyBuilder` generates valid ServerAuthorization YAML for all three modes
- Missing client specifications are rejected
- All generated YAML includes correct apiVersion and kind fields
- Tests cover valid configurations, validation errors, weight shifting, and YAML output correctness
