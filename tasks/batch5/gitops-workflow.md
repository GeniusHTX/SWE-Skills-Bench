# Task: Configure a GitOps Deployment Pipeline with Flux CD

## Background

Flux CD (https://github.com/fluxcd/flux2) is a GitOps toolkit for Kubernetes. This task requires creating a complete GitOps configuration for deploying a 3-tier web application (frontend, backend API, PostgreSQL database) using Flux CD custom resources. The configuration must include Kustomization resources, HelmRelease for the database, image automation for the backend, and a multi-environment (staging/production) promotion strategy.

## Files to Create/Modify

- `config/clusters/staging/flux-system/gotk-sync.yaml` (create) — Flux `GitRepository` source pointing to this repo and a root `Kustomization` that bootstraps all staging resources.
- `config/clusters/staging/apps/kustomization.yaml` (create) — Flux `Kustomization` for the staging apps namespace, referencing the app manifests with health checks and dependency ordering.
- `config/apps/base/frontend/deployment.yaml` (create) — Kubernetes Deployment for the frontend (nginx-based, 2 replicas, readiness probe, resource limits).
- `config/apps/base/frontend/service.yaml` (create) — ClusterIP Service for the frontend on port 80.
- `config/apps/base/backend/deployment.yaml` (create) — Kubernetes Deployment for the backend API (3 replicas, readiness/liveness probes, environment variables from ConfigMap and Secret).
- `config/apps/base/backend/service.yaml` (create) — ClusterIP Service for the backend on port 8080.
- `config/apps/base/backend/kustomization.yaml` (create) — Kustomize file listing backend resources.
- `config/apps/base/frontend/kustomization.yaml` (create) — Kustomize file listing frontend resources.
- `config/apps/overlays/staging/kustomization.yaml` (create) — Staging overlay: reduces replicas to 1, sets staging-specific environment variables, adds `environment: staging` labels.
- `config/apps/overlays/production/kustomization.yaml` (create) — Production overlay: 3 replicas, production environment variables, PodDisruptionBudget, adds `environment: production` labels.
- `config/infrastructure/db/helmrelease.yaml` (create) — Flux `HelmRelease` for PostgreSQL using the Bitnami chart with values for storage, auth credentials from a sealed secret.
- `config/infrastructure/db/helmrepository.yaml` (create) — Flux `HelmRepository` source for the Bitnami charts.
- `tests/test_gitops_workflow.py` (create) — Tests validating YAML syntax, required fields in Flux resources, and Kustomize overlay correctness.

## Requirements

### GitRepository and Bootstrap

- `GitRepository` named `flux-system` in namespace `flux-system`, interval `1m`, branch `main`.
- Root `Kustomization` references the `GitRepository`, path `./config/clusters/staging`, prune enabled, timeout `5m`.

### Application Deployments

- Frontend: image `nginx:1.25-alpine`, container port 80, readiness probe on `/`, resources: 128Mi memory request / 256Mi limit, 100m CPU request / 200m limit.
- Backend: image `myapp/backend:latest`, container port 8080, readiness probe on `/health`, liveness probe on `/health` with `initialDelaySeconds: 15`, env vars `DATABASE_URL` from ConfigMap `backend-config`, `DB_PASSWORD` from Secret `backend-secrets`.
- Both deployments include: `revisionHistoryLimit: 3`, rolling update strategy with `maxUnavailable: 0`, `maxSurge: 1`.

### HelmRelease for PostgreSQL

- Chart `postgresql` from Bitnami repo `https://charts.bitnami.com/bitnami`, version `13.x`.
- Values: `primary.persistence.size: 10Gi`, `auth.existingSecret: postgresql-credentials`, `auth.database: myapp`.
- Interval: `5m`, install remediation: retry 3 times, upgrade remediation: retry 3 times with `remediateLastFailure: true`.
- Dependency: the backend Kustomization depends on the database HelmRelease being ready.

### Multi-Environment Overlay

- Staging: 1 replica each service, `LOG_LEVEL=debug`, namespace `staging`.
- Production: 3 replicas each, `LOG_LEVEL=info`, namespace `production`, PodDisruptionBudget (minAvailable: 1 for frontend, 2 for backend).

### Expected Functionality

- `kustomize build config/apps/overlays/staging/` → valid YAML with 1-replica deployments and staging labels.
- `kustomize build config/apps/overlays/production/` → valid YAML with 3-replica deployments, PDB, and production labels.
- The Flux `Kustomization` establishes dependency ordering: database → backend → frontend.
- `HelmRelease` renders with correct chart reference, version, and remediation settings.

## Acceptance Criteria

- All YAML files are syntactically valid and parseable.
- `GitRepository` and root `Kustomization` correctly reference the repo and path.
- Application deployments include proper probes, resource limits, and rolling update strategy.
- Kustomize overlays correctly patch replicas, labels, and environment variables.
- `HelmRelease` references the correct chart with remediation configuration.
- Dependency ordering is explicitly defined (database before backend, backend before frontend).
- Tests verify YAML validity, required Flux fields, overlay patch correctness, and HelmRelease structure.
