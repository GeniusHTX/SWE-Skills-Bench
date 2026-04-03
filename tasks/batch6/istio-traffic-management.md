# Task: Configure Istio Traffic Management for a Canary Deployment with Circuit Breaking

## Background

An e-commerce platform's `checkout` service is being upgraded from v1 to v2. The deployment must use Istio for a gradual canary rollout (10% → 50% → 100%), with circuit breaking to protect against v2 failures, fault injection for testing, and a Gateway for external HTTPS access. The `checkout` service depends on `payment` and `inventory` services, both requiring DestinationRules with connection pooling.

## Files to Create/Modify

- `istio/gateway.yaml` (create) — Istio Gateway for external HTTPS ingress on `shop.example.com`
- `istio/checkout-vs.yaml` (create) — VirtualService routing traffic between checkout v1 (stable) and v2 (canary) with weighted splits
- `istio/checkout-dr.yaml` (create) — DestinationRule defining v1 and v2 subsets with circuit breaker and connection pool settings
- `istio/payment-vs.yaml` (create) — VirtualService for payment service with retry policy and timeout
- `istio/payment-dr.yaml` (create) — DestinationRule for payment service with circuit breaker
- `istio/inventory-vs.yaml` (create) — VirtualService for inventory service with timeout
- `istio/inventory-dr.yaml` (create) — DestinationRule for inventory with connection pool limits
- `istio/fault-injection.yaml` (create) — VirtualService for fault injection testing: 5% HTTP 503 errors on checkout v2, 2-second delay on payment for 10% of requests
- `istio/traffic-mirror.yaml` (create) — VirtualService that mirrors 100% of production checkout v1 traffic to v2 (shadow testing, before canary begins)
- `k8s/checkout-v1-deployment.yaml` (create) — Kubernetes Deployment for checkout v1 with Istio sidecar labels
- `k8s/checkout-v2-deployment.yaml` (create) — Kubernetes Deployment for checkout v2 with Istio sidecar labels

## Requirements

### Gateway (`istio/gateway.yaml`)

- Name: `shop-gateway`, namespace: `istio-system`.
- Selector: `istio: ingressgateway`.
- Servers:
  - Port 443 HTTPS, host `shop.example.com`, TLS mode `SIMPLE`, credentialName `shop-tls-cert`.
  - Port 80 HTTP, host `shop.example.com`, redirect to HTTPS (`httpsRedirect: true`).

### Checkout VirtualService (`istio/checkout-vs.yaml`)

- Hosts: `checkout`, bind to gateway `shop-gateway` for external access.
- HTTP route rules:

  **Rule 1 — Canary header override**: match requests with header `x-canary: true` → route 100% to checkout v2 subset (for testing before percentage rollout).

  **Rule 2 — Weighted canary split**:
  - Stage 1 (initial): checkout v1 weight 90, checkout v2 weight 10.
  - Stage 2 (after validation): v1 weight 50, v2 weight 50.
  - Stage 3 (full rollout): v1 weight 0, v2 weight 100.
  - (File should be set at Stage 1; comments indicate how to progress.)

  **Both rules**: timeout `10s`, retries with `attempts: 3`, `perTryTimeout: 3s`, `retryOn: "5xx,reset,connect-failure,retriable-4xx"`.

- Cors policy: `allowOrigins: [{ exact: "https://shop.example.com" }]`, `allowMethods: ["GET", "POST"]`, `allowHeaders: ["content-type", "x-canary"]`.

### Checkout DestinationRule (`istio/checkout-dr.yaml`)

- Host: `checkout`.
- Subsets:
  - `v1`: labels `version: v1`. Traffic policy: connection pool TCP `maxConnections: 100`, HTTP `http1MaxPendingRequests: 100`, `http2MaxRequests: 1000`.
  - `v2`: labels `version: v2`. Traffic policy: connection pool TCP `maxConnections: 50` (lower during canary), HTTP `http1MaxPendingRequests: 50`, `http2MaxRequests: 500`.
- Outlier detection (both subsets):
  - `consecutive5xxErrors: 3`
  - `interval: 10s`
  - `baseEjectionTime: 30s`
  - `maxEjectionPercent: 50`
  - `minHealthPercent: 30`

### Payment Service (`istio/payment-vs.yaml`, `istio/payment-dr.yaml`)

- VirtualService: route to `payment`, timeout `5s`, retries: 2 attempts, `perTryTimeout: 2s`, `retryOn: "5xx,retriable-4xx"`.
- DestinationRule: circuit breaker with `consecutive5xxErrors: 5`, `interval: 30s`, `baseEjectionTime: 60s`. Connection pool: TCP `maxConnections: 200`, HTTP `maxRetries: 3`.

### Inventory Service (`istio/inventory-vs.yaml`, `istio/inventory-dr.yaml`)

- VirtualService: route to `inventory`, timeout `3s`, no retries (inventory checks must be fast).
- DestinationRule: connection pool TCP `maxConnections: 150`, HTTP `http1MaxPendingRequests: 200`. Outlier detection: `consecutive5xxErrors: 5`, `interval: 15s`, `baseEjectionTime: 15s`.

### Fault Injection (`istio/fault-injection.yaml`)

- VirtualService for `checkout` (applied during testing only, annotated with `purpose: chaos-testing`):
  - HTTP fault: abort with status 503 for 5% of requests targeting v2 subset.
  - HTTP fault: delay of 2000ms for 10% of requests.
  - Match condition: header `x-test-chaos: enabled` (safety guard — only injects faults when header present).

### Traffic Mirroring (`istio/traffic-mirror.yaml`)

- VirtualService for `checkout`:
  - Route 100% traffic to v1 subset.
  - Mirror 100% to v2 subset (`mirror: { host: checkout, subset: v2 }`, `mirrorPercentage: { value: 100.0 }`).
  - Mirror responses are discarded (fire-and-forget shadow traffic).

### Kubernetes Deployments

- Both `checkout-v1` and `checkout-v2` Deployments must include label `version: v1` / `version: v2` on pod template (matching DestinationRule subset selectors).
- Both include label `app: checkout` for Service selector.
- v1: image `ghcr.io/myorg/checkout:1.8.0`, 3 replicas.
- v2: image `ghcr.io/myorg/checkout:2.0.0-rc1`, 1 replica (scale up as canary progresses).
- Both have Istio sidecar injection annotation.

### Expected Functionality

- External request to `https://shop.example.com/checkout` → Gateway → VirtualService → 90% to v1, 10% to v2.
- Request with header `x-canary: true` → 100% to v2 (regardless of weights).
- v2 returns 3 consecutive 5xx errors → outlier detection ejects v2 pods for 30 seconds.
- Payment service takes >5s → request times out, retried up to 2 times.
- Mirror mode: all traffic goes to v1, shadow copy sent to v2 for testing (v2 responses discarded).
- Fault injection with `x-test-chaos: enabled` header → 5% of v2 requests fail with 503, 10% have 2s delay.

## Acceptance Criteria

- Gateway configures HTTPS with TLS credentials and HTTP-to-HTTPS redirect.
- VirtualService implements weighted canary routing between v1 and v2 subsets with header-based override.
- DestinationRules define v1/v2 subsets with label selectors matching Kubernetes pod labels.
- Circuit breaker configured via outlier detection: 3 consecutive 5xx errors, 30s ejection, 50% max ejection.
- Connection pools configured per service with explicit TCP maxConnections and HTTP pending request limits.
- Timeouts set per service: checkout 10s, payment 5s, inventory 3s.
- Retries configured for checkout (3 attempts) and payment (2 attempts) with per-try timeouts.
- Fault injection is guarded by `x-test-chaos: enabled` header to prevent accidental activation.
- Traffic mirroring sends shadow traffic to v2 without affecting v1 responses.
- Kubernetes Deployments include `version` labels matching DestinationRule subset selectors.
