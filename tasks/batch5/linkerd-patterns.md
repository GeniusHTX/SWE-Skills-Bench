# Task: Implement Linkerd Service Profile and Traffic Policy Configuration

## Background

Linkerd (https://github.com/linkerd/linkerd2) is a lightweight service mesh for Kubernetes. This task requires creating Linkerd service profiles and traffic policies for a microservices application with 3 services (api-gateway, order-service, payment-service). The configuration must include per-route metrics, retries with budgets, timeouts, circuit-breaking via failure accrual, and traffic splitting for canary deployments.

## Files to Create/Modify

- `policy/profiles/api-gateway-profile.yaml` (create) — Linkerd `ServiceProfile` for api-gateway defining routes with per-route metrics, retry conditions, and timeouts.
- `policy/profiles/order-service-profile.yaml` (create) — `ServiceProfile` for order-service with routes including retry budgets and timeout overrides.
- `policy/profiles/payment-service-profile.yaml` (create) — `ServiceProfile` for payment-service with strict timeout on the `/charge` endpoint and no retries on POST routes.
- `policy/traffic-split/order-canary.yaml` (create) — Linkerd `TrafficSplit` (SMI spec) for canary deployment of order-service: 90% to stable, 10% to canary.
- `policy/authorization/server.yaml` (create) — Linkerd `Server` and `ServerAuthorization` resources restricting which services can call payment-service (only order-service allowed).
- `policy/authorization/authz-policy.yaml` (create) — `AuthorizationPolicy` with `MeshTLSAuthentication` ensuring mTLS identity-based access control for payment-service.
- `tests/test_linkerd_patterns.py` (create) — Tests validating YAML structure, required fields, and policy correctness.

## Requirements

### API Gateway ServiceProfile

- Resource: `ServiceProfile` for `api-gateway.default.svc.cluster.local`.
- Routes:
  - `GET /api/orders` — timeout 5s, retry on 5xx with `isRetryable: true`.
  - `GET /api/orders/{id}` — timeout 3s, retryable.
  - `POST /api/orders` — timeout 10s, **not** retryable (mutating operation).
  - `GET /api/health` — timeout 1s, not retryable.
- `retryBudget`: `retryRatio: 0.2`, `minRetriesPerSecond: 10`, `ttl: 10s`.

### Order Service ServiceProfile

- Routes:
  - `GET /orders` — timeout 3s, retryable.
  - `POST /orders` — timeout 8s, not retryable.
  - `GET /orders/{id}/status` — timeout 2s, retryable.
- `retryBudget`: `retryRatio: 0.1`, `minRetriesPerSecond: 5`, `ttl: 10s`.

### Payment Service ServiceProfile

- Routes:
  - `POST /charge` — timeout 15s, **not retryable** (financial transaction, must not duplicate charges).
  - `GET /charge/{id}` — timeout 3s, retryable.
  - `POST /refund` — timeout 15s, must be idempotent, retryable with idempotency header check.

### Traffic Split

- `TrafficSplit` resource for `order-service`:
  - Backend `order-service-stable`: weight 900 (90%).
  - Backend `order-service-canary`: weight 100 (10%).
- Both backends must be in the same namespace.

### Authorization Policy

- `Server` resource for payment-service on port 8080.
- `ServerAuthorization` allowing traffic only from service accounts matching `order-service` in namespace `default`.
- `AuthorizationPolicy` with `MeshTLSAuthentication` requiring identity `order-service.default.serviceaccount.identity.linkerd.cluster.local`.

### Expected Functionality

- `GET /api/orders` requests through api-gateway that receive a 503 → Linkerd retries automatically (up to retry budget).
- `POST /api/orders` requests that receive a 503 → no retry (not retryable).
- Traffic to order-service splits 90/10 between stable and canary versions.
- Direct calls from frontend to payment-service → rejected by authorization policy (only order-service allowed).

## Acceptance Criteria

- All ServiceProfiles define routes with correct path regex patterns and HTTP methods.
- Timeout and retry settings are per-route, with mutating endpoints marked as non-retryable.
- Retry budgets are configured with reasonable ratios and TTLs.
- TrafficSplit weights sum to 1000 and reference correct backend services.
- Authorization policy restricts payment-service access to order-service's identity.
- All YAML files are valid Kubernetes resources with correct apiVersion, kind, and metadata.
- Tests verify YAML structure, route definitions, weight sums, and authorization resource linkage.
