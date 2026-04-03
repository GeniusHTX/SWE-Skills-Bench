# Task: Build a Kubernetes Manifest Generator Using Kustomize Overlays

## Background

Kustomize (https://github.com/kubernetes-sigs/kustomize) is the standard tool for customizing Kubernetes YAML configurations. This task requires creating a Kustomize base and overlay structure that generates complete Kubernetes manifests for a web application (deployment, service, configmap, HPA, ingress) with environment-specific overlays for development, staging, and production.

## Files to Create/Modify

- `examples/webapp/base/deployment.yaml` (create) — Base Deployment: 2 replicas, container `webapp` with image `webapp:latest`, ports 8080 and 9090 (metrics), readiness/liveness probes, resource requests/limits.
- `examples/webapp/base/service.yaml` (create) — Base ClusterIP Service exposing port 8080.
- `examples/webapp/base/configmap.yaml` (create) — Base ConfigMap with keys: `LOG_LEVEL=info`, `DB_POOL_SIZE=5`, `CACHE_TTL=300`.
- `examples/webapp/base/hpa.yaml` (create) — HorizontalPodAutoscaler: min 2, max 10, target CPU utilization 70%.
- `examples/webapp/base/kustomization.yaml` (create) — Kustomize file listing all base resources, common labels `app: webapp`, and a `configMapGenerator` with a hash suffix.
- `examples/webapp/overlays/dev/kustomization.yaml` (create) — Dev overlay: 1 replica, no HPA, `LOG_LEVEL=debug`, `DB_POOL_SIZE=2`, namespace `dev`, image tag override to `webapp:dev`.
- `examples/webapp/overlays/dev/replica-patch.yaml` (create) — Strategic merge patch reducing replicas to 1.
- `examples/webapp/overlays/staging/kustomization.yaml` (create) — Staging overlay: 2 replicas, HPA min=2/max=5, `LOG_LEVEL=info`, namespace `staging`, image tag `webapp:staging-latest`.
- `examples/webapp/overlays/staging/hpa-patch.yaml` (create) — JSON6902 patch for HPA maxReplicas and CPU target.
- `examples/webapp/overlays/production/kustomization.yaml` (create) — Production overlay: 3 replicas, HPA min=3/max=20, `LOG_LEVEL=warn`, `DB_POOL_SIZE=20`, namespace `production`, ingress resource added, image tag `webapp:v1.2.3`.
- `examples/webapp/overlays/production/ingress.yaml` (create) — Ingress resource with TLS, host `webapp.example.com`, path `/` routing to the webapp service.
- `examples/webapp/overlays/production/pdb.yaml` (create) — PodDisruptionBudget with `minAvailable: 2`.
- `tests/test_k8s_manifest_generator.py` (create) — Tests that run `kustomize build` on each overlay and validate the output manifests.

## Requirements

### Base Resources

- Deployment: `app: webapp` label, container `webapp:latest`, ports `http: 8080`, `metrics: 9090`, readiness probe `GET /health` on 8080 every 10s, liveness probe `GET /health` with `initialDelaySeconds: 30`, resources: `requests: {cpu: 100m, memory: 128Mi}`, `limits: {cpu: 500m, memory: 512Mi}`.
- ConfigMap: generated with hash suffix via `configMapGenerator` (not a static ConfigMap resource), containing `LOG_LEVEL`, `DB_POOL_SIZE`, `CACHE_TTL`.
- HPA: `apiVersion: autoscaling/v2`, target deployment `webapp`, `minReplicas: 2`, `maxReplicas: 10`, metric CPU `averageUtilization: 70`.

### Dev Overlay

- Patches replicas to 1 using strategic merge patch.
- Removes HPA entirely (not needed in dev).
- Overrides ConfigMap values: `LOG_LEVEL=debug`, `DB_POOL_SIZE=2`.
- Sets namespace `dev` and image tag `webapp:dev`.

### Staging Overlay

- Keeps 2 replicas, patches HPA to `maxReplicas: 5`.
- Sets namespace `staging`, image tag `webapp:staging-latest`.
- Uses JSON6902 patch to modify HPA.

### Production Overlay

- 3 replicas, HPA min=3/max=20, CPU target 60%.
- Adds Ingress with TLS (secret `webapp-tls`), host `webapp.example.com`.
- Adds PodDisruptionBudget.
- Sets namespace `production`, image `webapp:v1.2.3`.
- ConfigMap: `LOG_LEVEL=warn`, `DB_POOL_SIZE=20`, `CACHE_TTL=600`.

### Expected Functionality

- `kustomize build examples/webapp/overlays/dev/` → outputs Deployment (1 replica, debug logging, dev image), Service, ConfigMap — no HPA.
- `kustomize build examples/webapp/overlays/production/` → outputs Deployment (3 replicas), Service, ConfigMap, HPA (max 20), Ingress with TLS, PDB — all in `production` namespace.
- ConfigMap names include a hash suffix that changes when values change (triggering rollout).

## Acceptance Criteria

- `kustomize build` succeeds for all three overlays without errors.
- Dev output has 1 replica, no HPA, debug logging, and dev namespace.
- Staging output has 2 replicas, HPA max 5, staging namespace.
- Production output has 3 replicas, HPA min 3/max 20, Ingress with TLS, PDB, production namespace.
- ConfigMap uses hash-suffixed naming via `configMapGenerator`.
- All environment-specific values (LOG_LEVEL, DB_POOL_SIZE, image tag) are correctly overridden.
- Tests validate the output of each overlay build for correct resource counts, namespace, replica counts, and configuration values.
