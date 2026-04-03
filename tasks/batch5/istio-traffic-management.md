# Task: Configure Istio Traffic Management for Canary Deployments and Fault Injection

## Background

Istio (https://github.com/istio/istio) is a service mesh providing traffic management, security, and observability. This task requires creating Istio traffic management resources for a microservices application with weighted routing (canary), fault injection for chaos testing, circuit breaking, and request-level routing based on headers. All resources target the `bookinfo` sample application (productpage, reviews, ratings, details services).

## Files to Create/Modify

- `samples/bookinfo/networking/destination-rules.yaml` (create) — `DestinationRule` resources for reviews (v1, v2, v3 subsets) and ratings (v1, v2 subsets) with connection pool settings and outlier detection.
- `samples/bookinfo/networking/virtual-service-canary.yaml` (create) — `VirtualService` for reviews: 80% traffic to v1, 15% to v2, 5% to v3. Header-based routing: requests with `x-canary: true` go to v3.
- `samples/bookinfo/networking/virtual-service-fault.yaml` (create) — `VirtualService` for ratings with fault injection: 10% of requests get a 7-second delay, 5% get HTTP 503 abort. Only applied when header `x-test-fault: enabled` is present.
- `samples/bookinfo/networking/gateway.yaml` (create) — Istio `Gateway` resource for ingress on port 80 and 443 (with TLS), host `bookinfo.example.com`.
- `samples/bookinfo/networking/virtual-service-ingress.yaml` (create) — `VirtualService` binding to the gateway, routing `/productpage` to productpage service, `/api/reviews` to reviews, `/api/ratings` to ratings.
- `samples/bookinfo/networking/circuit-breaker.yaml` (create) — `DestinationRule` for ratings with circuit breaker: `connectionPool` (maxConnections: 100, http1MaxPendingRequests: 10, http2MaxRequests: 1000), `outlierDetection` (consecutive5xxErrors: 3, interval: 30s, baseEjectionTime: 60s, maxEjectionPercent: 50).
- `tests/test_istio_traffic_management.py` (create) — Tests validating YAML structure, weight sums, fault injection percentages, and circuit breaker configuration.

## Requirements

### Destination Rules

- **reviews**: 3 subsets (`v1`, `v2`, `v3`) selected by label `version: v1/v2/v3`. Traffic policy: `connectionPool.http.h2UpgradePolicy: UPGRADE`.
- **ratings**: 2 subsets (`v1`, `v2`). Outlier detection: `consecutive5xxErrors: 3`, `interval: 30s`, `baseEjectionTime: 60s`, `maxEjectionPercent: 50`.

### Canary Virtual Service (Reviews)

- Default route: 80% to `v1`, 15% to `v2`, 5% to `v3`.
- Match rule: if header `x-canary` equals `true` → 100% to `v3` (overrides default weights).
- Match rule: if header `x-version` equals `v2` → 100% to `v2`.
- Timeout: 10s for all routes.
- Retry: 3 attempts on `5xx,connect-failure,refused-stream`, per-try timeout 3s.

### Fault Injection Virtual Service (Ratings)

- Match: header `x-test-fault: enabled`.
  - Fault delay: 7s fixed delay on 10% of requests (`percentage.value: 10`).
  - Fault abort: HTTP 503 on 5% of requests (`percentage.value: 5`).
- Non-matching requests (no header) → normal routing to ratings v1.

### Gateway

- Port 80: HTTP, host `bookinfo.example.com`.
- Port 443: HTTPS, `credentialName: bookinfo-tls`, mode `SIMPLE`, host `bookinfo.example.com`.

### Ingress Virtual Service

- Bound to the gateway.
- URI prefix `/productpage` → productpage service port 9080.
- URI prefix `/api/reviews` → reviews service port 9080 with rewrite `/reviews`.
- URI prefix `/api/ratings` → ratings service port 9080 with rewrite `/ratings`.

### Expected Functionality

- Normal traffic to reviews → 80% sees v1 (no stars), 15% sees v2 (black stars), 5% sees v3 (red stars).
- Request with `x-canary: true` → always sees v3 (red stars).
- Request to ratings with `x-test-fault: enabled` → 10% experience 7s delay, 5% receive 503 error.
- After 3 consecutive 5xx errors from a ratings pod → circuit breaker ejects the pod for 60s.

## Acceptance Criteria

- All YAML files have correct Istio `apiVersion` (`networking.istio.io/v1beta1`) and `kind`.
- Canary weights on reviews sum to 100 in the default route.
- Header-based match rules correctly override weight-based routing.
- Fault injection specifies both delay and abort with correct percentage values.
- Gateway defines both HTTP and HTTPS ports with TLS configuration.
- Circuit breaker destination rule includes connection pool limits and outlier detection.
- Tests validate resource structure, weight arithmetic, fault percentages, and TLS config.
