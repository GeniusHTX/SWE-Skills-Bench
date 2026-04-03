# Task: Generate Kubernetes Manifests for a Three-Tier E-Commerce Application

## Background

A three-tier e-commerce application needs production-ready Kubernetes manifests for deployment to a `production` namespace. The tiers are: a Next.js frontend (`storefront`), a FastAPI backend (`api`), and a PostgreSQL database (`db`). Each tier needs Deployment, Service, ConfigMap, and appropriate security contexts. The API tier needs a HorizontalPodAutoscaler, and the database tier needs a PersistentVolumeClaim.

## Files to Create/Modify

- `k8s/namespace.yaml` (create) — Namespace definition for `production`
- `k8s/storefront/deployment.yaml` (create) — Frontend Deployment with 3 replicas, resource limits, probes, security context
- `k8s/storefront/service.yaml` (create) — Frontend ClusterIP Service on port 80 → 3000
- `k8s/storefront/configmap.yaml` (create) — Frontend environment config: API_URL, NODE_ENV
- `k8s/api/deployment.yaml` (create) — API Deployment with 3 replicas, resource limits, probes, security context, envFrom ConfigMap and Secret
- `k8s/api/service.yaml` (create) — API ClusterIP Service on port 80 → 8000
- `k8s/api/configmap.yaml` (create) — API config: DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, REDIS_URL, LOG_LEVEL
- `k8s/api/secret.yaml` (create) — API secrets: DATABASE_PASSWORD, JWT_SECRET (base64 encoded placeholder values)
- `k8s/api/hpa.yaml` (create) — HorizontalPodAutoscaler: min 3, max 10, target CPU 70%, target memory 80%
- `k8s/db/statefulset.yaml` (create) — PostgreSQL StatefulSet with 1 replica, volumeClaimTemplate, init container for permissions
- `k8s/db/service.yaml` (create) — PostgreSQL headless Service on port 5432
- `k8s/db/configmap.yaml` (create) — PostgreSQL config: POSTGRES_DB, POSTGRES_USER
- `k8s/db/secret.yaml` (create) — PostgreSQL secret: POSTGRES_PASSWORD (base64 encoded)
- `k8s/db/pvc.yaml` (create) — PersistentVolumeClaim: 20Gi, ReadWriteOnce, storageClass `gp3`
- `k8s/ingress.yaml` (create) — Ingress with TLS termination, routing `/` to storefront and `/api/*` to api
- `k8s/networkpolicy.yaml` (create) — NetworkPolicies: storefront can reach api, api can reach db, db accepts only from api

## Requirements

### Namespace (`k8s/namespace.yaml`)

- Name: `production`
- Labels: `name: production`, `env: production`

### Storefront Deployment (`k8s/storefront/deployment.yaml`)

- Image: `ghcr.io/myorg/storefront:1.2.0` (pinned tag, not `:latest`)
- Replicas: 3
- Labels: `app: storefront`, `tier: frontend`, `version: "1.2.0"`
- Container port: 3000, named `http`
- Resources: requests `cpu: 200m, memory: 256Mi`, limits `cpu: 500m, memory: 512Mi`
- Liveness probe: HTTP GET `/health` port `http`, initialDelaySeconds 15, periodSeconds 10
- Readiness probe: HTTP GET `/ready` port `http`, initialDelaySeconds 5, periodSeconds 5
- Security context (pod level): `runAsNonRoot: true`, `fsGroup: 1001`
- Security context (container level): `runAsUser: 1001`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`
- Mount emmptyDir at `/tmp` for Next.js cache
- envFrom: `configMapRef` to `storefront-config`
- Rolling update strategy: `maxUnavailable: 1`, `maxSurge: 1`
- `topologySpreadConstraints`: spread by `topology.kubernetes.io/zone` with `maxSkew: 1`

### API Deployment (`k8s/api/deployment.yaml`)

- Image: `ghcr.io/myorg/api:2.0.3`
- Replicas: 3
- Container port: 8000, named `http`
- Resources: requests `cpu: 250m, memory: 512Mi`, limits `cpu: 1000m, memory: 1Gi`
- Liveness probe: HTTP GET `/health` port `http`, initialDelaySeconds 30, periodSeconds 10, failureThreshold 3
- Readiness probe: HTTP GET `/ready` port `http`, initialDelaySeconds 10, periodSeconds 5
- Startup probe: HTTP GET `/health` port `http`, failureThreshold 30, periodSeconds 10 (allows 5 min startup)
- envFrom: `configMapRef` → `api-config`, `secretRef` → `api-secret`
- Security context: same non-root pattern as storefront
- Pod anti-affinity: prefer scheduling on different nodes (`podAntiAffinity.preferredDuringSchedulingIgnoredDuringExecution`)

### HPA (`k8s/api/hpa.yaml`)

- `apiVersion: autoscaling/v2`
- Targets: Deployment `api`
- Min replicas: 3, max: 10
- Metrics:
  - CPU utilization: average 70%
  - Memory utilization: average 80%
- Scale-down behavior: stabilization window 300s, max 1 pod per 60s

### PostgreSQL StatefulSet (`k8s/db/statefulset.yaml`)

- Image: `postgres:16.2-alpine`
- Replicas: 1
- Service name: `db-headless`
- Container port: 5432
- Resources: requests `cpu: 500m, memory: 1Gi`, limits `cpu: 2000m, memory: 2Gi`
- Liveness probe: exec `pg_isready -U $POSTGRES_USER`, initialDelaySeconds 30
- envFrom: configMapRef `db-config`, secretRef `db-secret`
- Volume mount: `/var/lib/postgresql/data` from PVC
- `volumeClaimTemplates`: 20Gi, `storageClassName: gp3`, accessMode `ReadWriteOnce`
- Init container: `busybox`, runs `chown -R 999:999 /var/lib/postgresql/data` to set correct Postgres user permissions

### NetworkPolicies (`k8s/networkpolicy.yaml`)

- Policy 1 — `allow-storefront-to-api`: storefront pods (label `tier: frontend`) can send traffic to api pods (label `tier: backend`) on port 8000. All other ingress to api denied.
- Policy 2 — `allow-api-to-db`: api pods (label `tier: backend`) can send traffic to db pods (label `tier: database`) on port 5432. All other ingress to db denied.
- Policy 3 — `default-deny`: default deny all ingress in the `production` namespace.

### Ingress (`k8s/ingress.yaml`)

- `ingressClassName: nginx`
- TLS: host `shop.example.com`, secret `shop-tls-secret`
- Rules:
  - Host `shop.example.com`, path `/api` → service `api` port 80 (pathType `Prefix`)
  - Host `shop.example.com`, path `/` → service `storefront` port 80 (pathType `Prefix`)

### Expected Functionality

- `kubectl apply -f k8s/` → creates all resources in `production` namespace.
- Storefront pods run as non-root user 1001 with read-only filesystem.
- API scales from 3 to 10 pods based on CPU/memory pressure.
- Only storefront can reach API, only API can reach DB (network policies).
- Ingress routes `shop.example.com/api/*` to API service, everything else to storefront.
- PostgreSQL data persists across pod restarts via PVC.

## Acceptance Criteria

- All manifests use specific image tags, not `:latest`.
- All Deployments have resource requests and limits, liveness and readiness probes.
- Security contexts enforce `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`.
- HPA targets both CPU and memory with scale-down stabilization.
- StatefulSet uses `volumeClaimTemplates` for persistent PostgreSQL storage with `gp3` storage class.
- NetworkPolicies implement a default-deny policy with explicit allow rules for inter-tier communication.
- Ingress has TLS configuration and path-based routing.
- ConfigMaps and Secrets separate sensitive from non-sensitive configuration.
- Pod topology spread constraints or anti-affinity distribute pods across zones/nodes.
