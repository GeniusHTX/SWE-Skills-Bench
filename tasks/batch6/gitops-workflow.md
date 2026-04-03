# Task: Set Up a GitOps Workflow with ArgoCD for Multi-Environment Kubernetes Deployments

## Background

A microservices platform with 3 services (frontend, backend, worker) needs a GitOps workflow using ArgoCD for automated, declarative Kubernetes deployments across staging and production environments. The setup includes the App of Apps pattern, Kustomize overlays for environment-specific configuration, automated sync for staging, manual sync for production, and a notification system via Slack webhooks.

## Files to Create/Modify

- `argocd/projects/platform.yaml` (create) — ArgoCD AppProject restricting sources, destinations, and cluster resources
- `argocd/applications/root-app.yaml` (create) — App of Apps root application that manages all other applications
- `argocd/applications/staging/frontend.yaml` (create) — ArgoCD Application for frontend staging deployment
- `argocd/applications/staging/backend.yaml` (create) — ArgoCD Application for backend staging deployment
- `argocd/applications/staging/worker.yaml` (create) — ArgoCD Application for worker staging deployment
- `argocd/applications/production/frontend.yaml` (create) — ArgoCD Application for frontend production deployment
- `argocd/applications/production/backend.yaml` (create) — ArgoCD Application for backend production deployment
- `argocd/applications/production/worker.yaml` (create) — ArgoCD Application for worker production deployment
- `apps/base/frontend/deployment.yaml` (create) — Base Kubernetes Deployment for frontend
- `apps/base/frontend/service.yaml` (create) — Base Service for frontend
- `apps/base/frontend/kustomization.yaml` (create) — Base Kustomization for frontend
- `apps/base/backend/deployment.yaml` (create) — Base Deployment for backend
- `apps/base/backend/service.yaml` (create) — Base Service for backend
- `apps/base/backend/kustomization.yaml` (create) — Base Kustomization for backend
- `apps/overlays/staging/frontend/kustomization.yaml` (create) — Staging overlay: 2 replicas, staging image tag, staging ConfigMap patches
- `apps/overlays/staging/backend/kustomization.yaml` (create) — Staging overlay: 2 replicas, staging config
- `apps/overlays/production/frontend/kustomization.yaml` (create) — Production overlay: 5 replicas, production image tag, production ConfigMap
- `apps/overlays/production/backend/kustomization.yaml` (create) — Production overlay: 5 replicas, production config
- `argocd/notifications/config.yaml` (create) — ArgoCD Notifications ConfigMap with Slack templates and triggers

## Requirements

### ArgoCD AppProject (`argocd/projects/platform.yaml`)

- Name: `platform`
- Source repos: only `https://github.com/myorg/gitops-repo.git`
- Destinations: cluster `https://kubernetes.default.svc`, namespaces `staging` and `production` only.
- Allowed cluster resources: `Namespace`, `ClusterRole`, `ClusterRoleBinding`.
- Allowed namespaced resources: `Deployment`, `Service`, `ConfigMap`, `Secret`, `Ingress`, `HorizontalPodAutoscaler`, `PodDisruptionBudget`.
- Roles:
  - `staging-deployer`: allow `sync` on `staging/*` applications.
  - `production-deployer`: allow `sync` on `production/*` applications, requires RBAC group `platform-leads`.

### Root Application (`argocd/applications/root-app.yaml`)

- App of Apps pattern: source path `argocd/applications`, monitors both `staging/` and `production/` subdirectories.
- Automated sync with prune and self-heal.
- Automated sync only applies to the root app — child apps define their own sync policies.

### Staging Applications

Each staging ArgoCD Application:
- Project: `platform`
- Source: repo `https://github.com/myorg/gitops-repo.git`, path `apps/overlays/staging/{service}`, targetRevision `main`
- Destination: server `https://kubernetes.default.svc`, namespace `staging`
- Sync policy: `automated: { prune: true, selfHeal: true }`, syncOptions: `["CreateNamespace=true", "ApplyOutOfSyncOnly=true"]`
- Retry: limit 5, backoff duration 5s, factor 2, maxDuration 3m
- Health check: wait for Deployment rollout

### Production Applications

Each production ArgoCD Application:
- Same as staging except:
  - Destination namespace: `production`
  - Source path: `apps/overlays/production/{service}`
  - Sync policy: **NOT automated** (manual sync required)
  - Sync windows: only allow sync Monday-Friday 09:00-17:00 UTC (`syncPolicy.syncWindows`)
  - Annotations: `notifications.argoproj.io/subscribe.on-sync-succeeded.slack: platform-deploys`

### Base Manifests (`apps/base/`)

Frontend base:
- Deployment: image `ghcr.io/myorg/frontend:PLACEHOLDER`, port 3000, resources requests `cpu: 100m, memory: 128Mi`, probes at `/healthz`.
- Service: ClusterIP, port 80 → 3000.

Backend base:
- Deployment: image `ghcr.io/myorg/backend:PLACEHOLDER`, port 8000, env from ConfigMap `backend-config`, resources requests `cpu: 200m, memory: 256Mi`, probes at `/health`.
- Service: ClusterIP, port 80 → 8000.

### Kustomize Overlays

Staging overlays patch:
- Image tag: `images: [{ name: ghcr.io/myorg/frontend, newTag: staging-latest }]`
- Replicas: 2 per service
- ConfigMap generator: `LOG_LEVEL=debug`, `DATABASE_URL=postgresql://staging-db:5432/app`
- Namespace: `staging`
- Common labels: `env: staging`

Production overlays patch:
- Image tag: `images: [{ name: ghcr.io/myorg/frontend, newTag: v1.5.2 }]` (pinned version)
- Replicas: 5 per service
- ConfigMap generator: `LOG_LEVEL=warn`, `DATABASE_URL=postgresql://production-db:5432/app`
- Namespace: `production`
- Common labels: `env: production`
- Additional resource: `PodDisruptionBudget` with `minAvailable: 3`

### Notifications (`argocd/notifications/config.yaml`)

- Slack webhook integration using secret `argocd-notifications-secret` key `slack-webhook`.
- Templates:
  - `app-sync-succeeded`: `":white_check_mark: {{.app.metadata.name}} synced to {{.app.status.sync.revision | trunc 7}} in {{.app.spec.destination.namespace}}"`
  - `app-sync-failed`: `":x: {{.app.metadata.name}} sync failed in {{.app.spec.destination.namespace}}: {{.app.status.operationState.message}}"`
  - `app-health-degraded`: `":warning: {{.app.metadata.name}} health degraded in {{.app.spec.destination.namespace}}"`
- Triggers:
  - `on-sync-succeeded`: when `app.status.operationState.phase == Succeeded`
  - `on-sync-failed`: when `app.status.operationState.phase == Failed`
  - `on-health-degraded`: when `app.status.health.status == Degraded`

### Expected Functionality

- Push to `main` branch updating `apps/overlays/staging/frontend/kustomization.yaml` with new image tag → ArgoCD auto-syncs staging frontend, sends Slack success notification.
- Production apps show as `OutOfSync` in ArgoCD UI after staging changes are verified → manual sync triggers production deployment within sync window.
- Deleting a manifest from Git → ArgoCD prunes the corresponding resource (automated prune enabled).
- Health check degradation → Slack notification via `app-health-degraded` trigger.
- Attempt to deploy to namespace `dev` → rejected by AppProject destination restrictions.

## Acceptance Criteria

- AppProject restricts source repos, destination namespaces, and allowed resource types.
- App of Apps root application manages all child applications from `argocd/applications/` directory.
- Staging applications use automated sync with prune, self-heal, and retry backoff.
- Production applications require manual sync and restrict sync to business hours (Mon-Fri 09:00-17:00 UTC).
- Kustomize base manifests define shared configuration; overlays customize replicas, image tags, ConfigMaps, and namespace per environment.
- Production overlays include PodDisruptionBudget with `minAvailable: 3`.
- Staging uses floating tags (`staging-latest`); production uses pinned version tags (`v1.5.2`).
- ArgoCD Notifications send Slack messages on sync success, sync failure, and health degradation.
- Notification templates include app name, target namespace, and git revision.
