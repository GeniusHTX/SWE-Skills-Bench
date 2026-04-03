# Task: Configure Linkerd Service Mesh for a Microservices Application with Traffic Splits and Authorization

## Background

A microservices application with 4 services (gateway, orders, payments, notifications) needs Linkerd service mesh configuration for automatic mTLS, per-route metrics via ServiceProfiles, canary deployment via TrafficSplit, and zero-trust authorization policies. The application runs in the `ecommerce` namespace on Kubernetes.

## Files to Create/Modify

- `linkerd/namespace.yaml` (create) — Namespace `ecommerce` with Linkerd injection annotation
- `linkerd/service-profiles/gateway-sp.yaml` (create) — ServiceProfile for gateway with route definitions and timeouts
- `linkerd/service-profiles/orders-sp.yaml` (create) — ServiceProfile for orders service with retry configuration
- `linkerd/service-profiles/payments-sp.yaml` (create) — ServiceProfile for payments service (no retries for POST)
- `linkerd/traffic-split/orders-canary.yaml` (create) — TrafficSplit for orders service canary deployment (90/10 split)
- `linkerd/authorization/server-orders.yaml` (create) — Server resource defining orders service ports
- `linkerd/authorization/authz-orders.yaml` (create) — ServerAuthorization allowing only gateway to access orders
- `linkerd/authorization/authz-payments.yaml` (create) — ServerAuthorization allowing only orders to access payments
- `linkerd/authorization/authz-notifications.yaml` (create) — ServerAuthorization allowing only orders and payments to access notifications
- `linkerd/authorization/default-deny.yaml` (create) — Default deny authorization policy for the namespace

## Requirements

### Namespace (`linkerd/namespace.yaml`)

- Name: `ecommerce`
- Annotation: `linkerd.io/inject: enabled` (automatic sidecar injection for all pods in namespace)
- Labels: `linkerd.io/is-control-plane: "false"`

### ServiceProfile — Gateway (`linkerd/service-profiles/gateway-sp.yaml`)

- Full name: `gateway.ecommerce.svc.cluster.local`
- Routes:
  - `GET /api/orders` — isRetryable: true, timeout: 10s
  - `POST /api/orders` — isRetryable: false, timeout: 15s
  - `GET /api/orders/{id}` — pathRegex: `/api/orders/[^/]+`, isRetryable: true, timeout: 5s
  - `GET /api/payments/{id}` — pathRegex: `/api/payments/[^/]+`, isRetryable: true, timeout: 5s
  - `GET /health` — isRetryable: false, timeout: 2s
- Response classes: 5xx responses (status min 500, max 599) marked as `isFailure: true` on all routes.
- Retry budget: `retryRatio: 0.2`, `minRetriesPerSecond: 10`, `ttl: 10s`.

### ServiceProfile — Orders (`linkerd/service-profiles/orders-sp.yaml`)

- Full name: `orders.ecommerce.svc.cluster.local`
- Routes:
  - `GET /orders` — isRetryable: true, timeout: 5s
  - `POST /orders` — isRetryable: false, timeout: 10s
  - `GET /orders/{id}` — pathRegex: `/orders/[^/]+`, isRetryable: true, timeout: 3s
  - `PUT /orders/{id}/status` — pathRegex: `/orders/[^/]+/status`, isRetryable: false, timeout: 5s
  - `DELETE /orders/{id}` — pathRegex: `/orders/[^/]+`, isRetryable: false, timeout: 5s
- Retry budget: `retryRatio: 0.2`, `minRetriesPerSecond: 5`, `ttl: 10s`.

### ServiceProfile — Payments (`linkerd/service-profiles/payments-sp.yaml`)

- Full name: `payments.ecommerce.svc.cluster.local`
- Routes:
  - `POST /payments` — isRetryable: false (payment operations must not be retried), timeout: 30s
  - `GET /payments/{id}` — pathRegex: `/payments/[^/]+`, isRetryable: true, timeout: 5s
  - `POST /payments/{id}/refund` — pathRegex: `/payments/[^/]+/refund`, isRetryable: false, timeout: 30s
- Response classes: 5xx as failure.
- No retry budget (retries disabled for payment mutations).

### TrafficSplit — Orders Canary (`linkerd/traffic-split/orders-canary.yaml`)

- `apiVersion: split.smi-spec.io/v1alpha1`, kind `TrafficSplit`.
- Service: `orders`
- Backends:
  - `orders-stable` — weight 900 (90%)
  - `orders-canary` — weight 100 (10%)
- Requires two Kubernetes Services: `orders-stable` and `orders-canary` selecting pods by `version: stable` and `version: canary` labels respectively.

### Authorization — Server (`linkerd/authorization/server-orders.yaml`)

- `apiVersion: policy.linkerd.io/v1beta1`, kind `Server`.
- Name: `orders-http`, namespace: `ecommerce`.
- Pod selector: `matchLabels: { app: orders }`.
- Port: 8080, protocol: HTTP/1.

### Authorization — Orders (`linkerd/authorization/authz-orders.yaml`)

- Kind `ServerAuthorization`.
- Server ref: `orders-http`.
- Client: `meshTLS: { serviceAccounts: [{ name: "gateway", namespace: "ecommerce" }] }` — only the gateway service account can access orders.

### Authorization — Payments (`linkerd/authorization/authz-payments.yaml`)

- Server: `payments-http` (define matching Server resource inline or separately).
- Client: only `orders` service account can access payments.

### Authorization — Notifications (`linkerd/authorization/authz-notifications.yaml`)

- Server: `notifications-http`.
- Client: both `orders` and `payments` service accounts can access notifications.

### Default Deny (`linkerd/authorization/default-deny.yaml`)

- `Server` resource selecting all pods in `ecommerce` namespace (`podSelector: {}`) with `accessPolicy: deny`.
- This ensures any service not explicitly authorized is denied access (zero-trust).

### Expected Functionality

- All pods in `ecommerce` namespace get Linkerd proxy injected automatically.
- `GET /api/orders` through gateway → retried if 5xx (up to retry budget), timeout 10s.
- `POST /payments` through orders → NOT retried if fails, timeout 30s.
- Traffic to orders service → 90% to `orders-stable`, 10% to `orders-canary`.
- HTTP request from `gateway` to `orders` → allowed by ServerAuthorization.
- HTTP request from `notifications` to `orders` → denied (not in allowed service accounts).
- All inter-service communication uses automatic mTLS via Linkerd identity.

## Acceptance Criteria

- Namespace has `linkerd.io/inject: enabled` annotation for automatic proxy injection.
- ServiceProfiles define per-route metrics, timeouts, and retry configuration for gateway, orders, and payments services.
- GET endpoints are marked `isRetryable: true`; mutation endpoints (POST, PUT, DELETE) are `isRetryable: false`.
- Payment service POST routes have no retry budget and 30s timeout for long-running payment processing.
- TrafficSplit configures 90/10 weighted split between `orders-stable` and `orders-canary` backends.
- Server resources define port and protocol for each service.
- ServerAuthorization restricts access via mTLS service account identity: gateway→orders, orders→payments, orders+payments→notifications.
- Default deny Server resource ensures zero-trust baseline — all unauthorized traffic is rejected.
- Retry budgets limit retry amplification to 20% of original traffic.
