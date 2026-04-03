# Task: Create Linkerd Service Mesh Configuration with Service Profiles and Traffic Splits for Linkerd2

## Background

The Linkerd2 repository (https://github.com/linkerd/linkerd2) is a lightweight, security-focused service mesh for Kubernetes. A new set of example manifests is needed that demonstrates a complete service mesh configuration for a three-service application (frontend, API, database proxy), including service profiles with per-route metrics and retries, traffic splits for canary deployments, server authorization policies for zero-trust networking, and multi-service observability configuration.

## Files to Create/Modify

- `examples/mesh-demo/manifests/namespace.yaml` (create) — Namespace with Linkerd injection annotation
- `examples/mesh-demo/manifests/frontend.yaml` (create) — Frontend Deployment and Service with Linkerd annotations
- `examples/mesh-demo/manifests/api.yaml` (create) — API Deployment and Service with Linkerd annotations
- `examples/mesh-demo/manifests/db-proxy.yaml` (create) — Database proxy Deployment and Service
- `examples/mesh-demo/profiles/api-profile.yaml` (create) — ServiceProfile for API with per-route config, retries, timeouts
- `examples/mesh-demo/profiles/frontend-profile.yaml` (create) — ServiceProfile for frontend
- `examples/mesh-demo/traffic/canary-split.yaml` (create) — TrafficSplit for canary deployment of API v2
- `examples/mesh-demo/policy/server.yaml` (create) — Server and ServerAuthorization resources for zero-trust policy
- `tests/test_linkerd_patterns.py` (create) — Python tests validating manifest structure, service profiles, and policy correctness

## Requirements

### Namespace and Injection

- Namespace `mesh-demo` with annotation `linkerd.io/inject: enabled`
- All Deployments must have the `linkerd.io/inject: enabled` pod template annotation

### Service Deployments

- **Frontend**: image `mesh-demo/frontend:1.0.0`, port 8080, 2 replicas, liveness/readiness probes at `/health`, CPU request 100m, memory request 128Mi
- **API** (stable): image `mesh-demo/api:1.0.0`, port 8081, 2 replicas, probes at `/healthz`, name `api`, label `version: v1`
- **API** (canary): image `mesh-demo/api:2.0.0`, 1 replica, same port and probes, name `api-canary`, label `version: v2`
- **DB Proxy**: image `mesh-demo/db-proxy:1.0.0`, port 5432, 1 replica, TCP liveness probe on port 5432

### Service Profiles

**API ServiceProfile** (`api.mesh-demo.svc.cluster.local`):
- Route `GET /api/users`: retryable, timeout 5s, response class 500–599 as failure
- Route `POST /api/users`: NOT retryable, timeout 10s
- Route `GET /api/users/{id}`: retryable, timeout 3s, pathRegex `/api/users/[^/]+`
- Route `DELETE /api/users/{id}`: NOT retryable, timeout 5s
- Retry budget: retryRatio 0.2, minRetriesPerSecond 10, ttl 10s

**Frontend ServiceProfile** (`frontend.mesh-demo.svc.cluster.local`):
- Route `GET /`: timeout 10s, retryable
- Route `GET /static/{path}`: timeout 30s, NOT retryable

### Traffic Split (Canary)

- TrafficSplit `api-canary` splitting traffic to `api` service:
  - Backend `api` (stable): weight 900
  - Backend `api-canary`: weight 100
- This produces a 90/10 traffic split

### Zero-Trust Policy

- Server resource `api-server` for port 8081 on pods labeled `app: api`
- ServerAuthorization `allow-frontend-to-api`: allows only pods with serviceaccount `frontend` in namespace `mesh-demo` to access `api-server`
- ServerAuthorization `allow-prometheus`: allows pods with serviceaccount `prometheus` in namespace `monitoring` to scrape metrics on port 4191

### Expected Functionality

- Applying all manifests to a Linkerd-enabled cluster injects sidecar proxies into all pods
- The API service profile enables per-route metrics, retries for GET routes, and enforces timeouts
- Traffic split sends 90% of API traffic to v1 and 10% to v2
- Server authorization restricts API access to the frontend service only; other services are denied by default

## Acceptance Criteria

- All YAML manifests are valid and use correct Linkerd API versions (`linkerd.io/v1alpha2` for ServiceProfile, `split.smi-spec.io/v1alpha1` for TrafficSplit, `policy.linkerd.io/v1beta3` for Server/ServerAuthorization)
- Namespace has Linkerd injection annotation; all pod templates have injection enabled
- Service profiles define correct routes with appropriate retry/timeout configuration and retry budget
- Traffic split weights sum to 1000 with a 90/10 distribution
- Server authorization policies restrict access by service account
- Tests validate YAML structure, API versions, route definitions, traffic split weights, and policy rules
