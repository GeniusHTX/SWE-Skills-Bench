# Task: Implement Traffic Management Policies for the Bookinfo Application

## Background

The Istio service mesh repository (`istio/istio`) provides networking APIs under `networking/` and pilot configuration under `pilot/`. The `bookinfo` sample application needs a complete set of traffic management resources — VirtualServices, DestinationRules, and a Gateway — to support canary rollout of the `reviews` service v3, circuit breaking on the `ratings` service, and fault injection testing on the `productpage` → `details` call path.

## Files to Create/Modify

- `samples/bookinfo/networking/reviews-canary.yaml` (new) — VirtualService and DestinationRule for weighted canary rollout of the reviews service between v2 (stable) and v3 (canary)
- `samples/bookinfo/networking/ratings-circuit-breaker.yaml` (new) — DestinationRule with connection pool limits and outlier detection for the ratings service
- `samples/bookinfo/networking/details-fault-injection.yaml` (new) — VirtualService injecting both latency and abort faults on the details service for chaos testing
- `samples/bookinfo/networking/bookinfo-gateway.yaml` (new) — Gateway and VirtualService for HTTPS ingress routing to the productpage service
- `tests/test_istio_traffic_management.py` (new) — Unit tests validating YAML structure, field values, and cross-resource consistency

## Requirements

### Canary Rollout — `reviews-canary.yaml`

- Define a VirtualService named `reviews-canary` targeting host `reviews` in namespace `bookinfo`
- Route 80% of traffic to subset `stable` (version: v2) and 20% to subset `canary` (version: v3)
- Include a header-based match rule: requests with header `x-canary: true` must route 100% to subset `canary`, placed before the weighted default route
- Define a DestinationRule named `reviews-dr` for host `reviews` with three subsets: `v1` (version: v1), `stable` (version: v2), `canary` (version: v3)
- The DestinationRule must set a `trafficPolicy` with `connectionPool.tcp.maxConnections: 100` and `connectionPool.http.http2MaxRequests: 1000`

### Circuit Breaker — `ratings-circuit-breaker.yaml`

- Define a DestinationRule named `ratings-cb` for host `ratings` in namespace `bookinfo`
- Set `connectionPool.tcp.maxConnections` to 50
- Set `connectionPool.http.http1MaxPendingRequests` to 50, `http2MaxRequests` to 500, `maxRequestsPerConnection` to 5, and `maxRetries` to 3
- Configure `outlierDetection` with `consecutive5xxErrors: 3`, `interval: 15s`, `baseEjectionTime: 30s`, `maxEjectionPercent: 40`, and `minHealthPercent: 20`

### Fault Injection — `details-fault-injection.yaml`

- Define a VirtualService named `details-fault` targeting host `details` in namespace `bookinfo`
- Inject a fixed delay of `3s` on 15% of requests
- Inject an HTTP 503 abort on 5% of requests
- Both faults must apply to the same `http` route entry, with the route destination set to host `details` subset `v1`
- Include a `timeout: 10s` and a `retries` block with `attempts: 2`, `perTryTimeout: 4s`, and `retryOn: 5xx,connect-failure`

### Ingress Gateway — `bookinfo-gateway.yaml`

- Define a Gateway named `bookinfo-gateway` selecting `istio: ingressgateway`
- Configure a server on port 443 (HTTPS) with TLS mode `SIMPLE` and `credentialName: bookinfo-tls-secret`, accepting host `bookinfo.example.com`
- Configure a second server on port 80 (HTTP) accepting the same host, with an `httpsRedirect: true` in the `tls` section
- Define a VirtualService named `bookinfo-vs` bound to `bookinfo-gateway` for host `bookinfo.example.com`
- Route requests with URI prefix `/api/v1/reviews` to service `reviews` port 9080
- Route requests with URI prefix `/api/v1/ratings` to service `ratings` port 9080
- Route all other requests (prefix `/`) to service `productpage` port 9080

### YAML Quality

- All resources must use `apiVersion: networking.istio.io/v1beta1`
- Every resource must have `metadata.namespace: bookinfo` explicitly set
- Multi-document YAML files must separate resources with `---`
- No resource may duplicate a `metadata.name` within the same file

### Expected Functionality

- HTTP request with header `x-canary: true` to reviews → routed to reviews v3 pod exclusively
- HTTP request without canary header to reviews → 80% to v2 pods, 20% to v3 pods
- Ratings service receiving >50 concurrent TCP connections → excess connections rejected by connection pool
- Ratings endpoint returning 3 consecutive 5xx responses → pod ejected from load balancing for 30 seconds
- Request to details service → 15% of requests experience 3-second added latency; 5% receive HTTP 503
- HTTPS request to `bookinfo.example.com/api/v1/reviews` → forwarded to reviews service on port 9080
- HTTP request to `bookinfo.example.com` on port 80 → 301 redirect to HTTPS
- Request to `bookinfo.example.com/unknown-path` → forwarded to productpage service

## Acceptance Criteria

- All four YAML files parse without errors and contain valid Istio networking resources with `apiVersion: networking.istio.io/v1beta1`
- `reviews-canary.yaml` defines both a VirtualService with weighted routing (80/20) and header-match override, and a DestinationRule with three labeled subsets
- `ratings-circuit-breaker.yaml` defines a DestinationRule with connection pool limits and outlier detection thresholds matching the specified values
- `details-fault-injection.yaml` defines a VirtualService with simultaneous delay and abort fault injection plus timeout and retry configuration
- `bookinfo-gateway.yaml` defines a Gateway with HTTPS and HTTP-redirect servers, and a VirtualService with three URI-prefix route rules
- Every resource sets `metadata.namespace: bookinfo`
- Tests in `tests/test_istio_traffic_management.py` pass, validating resource structure and field correctness
