# Task: Implement Istio Traffic Management Manifests for a Bookinfo-Style Application

## Background

The Istio repository (https://github.com/istio/istio) is a service mesh platform for Kubernetes. A new set of Istio traffic management manifests is needed for a three-service application (frontend, reviews, ratings), demonstrating VirtualService routing, DestinationRules with circuit breaking, canary deployments with weighted traffic splitting, fault injection for chaos testing, and traffic mirroring for production verification.

## Files to Create/Modify

- `samples/traffic-demo/base/deployments.yaml` (create) — Deployments for frontend, reviews-v1, reviews-v2, and ratings services
- `samples/traffic-demo/base/services.yaml` (create) — Kubernetes Services for all three services
- `samples/traffic-demo/networking/gateway.yaml` (create) — Istio Gateway for external traffic ingress
- `samples/traffic-demo/networking/virtualservices.yaml` (create) — VirtualService resources with routing rules, canary weights, and fault injection
- `samples/traffic-demo/networking/destination-rules.yaml` (create) — DestinationRules with subsets, circuit breakers, and connection pool settings
- `samples/traffic-demo/networking/traffic-mirror.yaml` (create) — VirtualService with traffic mirroring to reviews-v2
- `tests/test_istio_traffic_management.py` (create) — Python tests validating YAML structure and Istio resource correctness

## Requirements

### Service Deployments

- **Frontend**: image `traffic-demo/frontend:1.0.0`, port 8080, 2 replicas, labels `app: frontend`, `version: v1`
- **Reviews v1**: image `traffic-demo/reviews:1.0.0`, port 8081, 2 replicas, labels `app: reviews`, `version: v1`
- **Reviews v2**: image `traffic-demo/reviews:2.0.0`, port 8081, 1 replica, labels `app: reviews`, `version: v2`
- **Ratings**: image `traffic-demo/ratings:1.0.0`, port 8082, 2 replicas, labels `app: ratings`, `version: v1`
- All Deployments must include `sidecar.istio.io/inject: "true"` annotation

### Gateway

- Name: `traffic-demo-gateway`
- Selector: `istio: ingressgateway`
- Server: port 80, HTTP protocol, hosts `["traffic-demo.example.com"]`

### VirtualService Routing

**Frontend VirtualService** (`traffic-demo.example.com`):
- Bound to `traffic-demo-gateway`
- Route all traffic to frontend service, port 8080

**Reviews VirtualService** (`reviews`):
- Default: route 90% to subset `v1`, 10% to subset `v2` (canary)
- Header-based routing: requests with header `end-user: tester` route 100% to `v2`
- Timeout: 5 seconds
- Retries: 3 attempts, per-try timeout 2s, retry on `5xx,reset,connect-failure`

**Ratings VirtualService** (`ratings`):
- Fault injection: for 10% of requests, inject a 500 error (abort); for 5% of requests, inject a 3-second delay (fixedDelay)
- Route all remaining traffic to ratings v1

### DestinationRules

**Reviews DestinationRule**:
- Subsets: `v1` (label `version: v1`), `v2` (label `version: v2`)
- Connection pool: TCP maxConnections 100, HTTP http1MaxPendingRequests 100, http2MaxRequests 1000
- Outlier detection: consecutive5xxErrors 5, interval 30s, baseEjectionTime 30s, maxEjectionPercent 50

**Ratings DestinationRule**:
- Subset: `v1` (label `version: v1`)
- Circuit breaker: consecutive5xxErrors 3, interval 10s, baseEjectionTime 60s

### Traffic Mirroring

- A separate VirtualService `reviews-mirror` that routes 100% of traffic to `reviews v1` and mirrors to `reviews v2` with `mirrorPercentage: 100`

### Expected Functionality

- External traffic hitting `traffic-demo.example.com` enters via the Gateway and reaches the frontend
- 90% of internal reviews traffic goes to v1, 10% to v2 (canary deployment)
- Requests with header `end-user: tester` always reach reviews v2
- 10% of ratings requests see a 500 error fault; 5% see a 3-second delay
- Traffic mirroring sends a copy of all reviews traffic to v2 without affecting the primary routing

## Acceptance Criteria

- All YAML manifests are valid with correct Istio API versions (`networking.istio.io/v1beta1`)
- Gateway correctly exposes the application on the specified host and port
- VirtualService routing rules implement canary weights, header-based routing, retries, and timeouts
- Fault injection is configured for both abort and delay on the ratings service
- DestinationRules define correct subsets, connection pool limits, and outlier detection settings
- Traffic mirroring VirtualService correctly mirrors traffic without affecting the primary route
- Tests validate YAML structure, API versions, weight percentages summing to 100, and resource references
