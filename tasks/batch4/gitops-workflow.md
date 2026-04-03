# Task: Implement GitOps Application Deployment Manifests with Multi-Environment Promotion for Flux CD

## Background

The Flux CD repository (https://github.com/fluxcd/flux2) is a GitOps toolkit for Kubernetes. A new set of GitOps deployment manifests is needed for a sample microservices application deployed across three environments (development, staging, production), using Kustomize overlays for environment-specific configuration, progressive promotion with health gates, and automated image update automation.

## Files to Create/Modify

- `examples/gitops-demo/base/deployment.yaml` (create) — Base Deployment manifest for the sample web application
- `examples/gitops-demo/base/service.yaml` (create) — Base Service manifest (ClusterIP)
- `examples/gitops-demo/base/kustomization.yaml` (create) — Base Kustomize configuration
- `examples/gitops-demo/overlays/development/kustomization.yaml` (create) — Development overlay with single replica, debug logging, relaxed resources
- `examples/gitops-demo/overlays/staging/kustomization.yaml` (create) — Staging overlay with 2 replicas, info logging, moderate resources
- `examples/gitops-demo/overlays/production/kustomization.yaml` (create) — Production overlay with 3 replicas, warn logging, strict resources, PodDisruptionBudget
- `examples/gitops-demo/overlays/production/pdb.yaml` (create) — PodDisruptionBudget for production
- `examples/gitops-demo/flux/gitrepository.yaml` (create) — Flux GitRepository source pointing to the demo repo
- `examples/gitops-demo/flux/kustomizations.yaml` (create) — Flux Kustomization resources for all three environments with dependencies and health checks
- `examples/gitops-demo/flux/image-update.yaml` (create) — Flux ImageRepository, ImagePolicy, and ImageUpdateAutomation for automatic image tag updates
- `tests/test_gitops_workflow.py` (create) — Python tests validating YAML structure, Kustomize overlays, and Flux resource correctness

## Requirements

### Base Manifests

- Deployment: `app-name: gitops-demo`, container image `ghcr.io/example/gitops-demo:1.0.0`, port 8080, liveness probe at `/healthz`, readiness probe at `/readyz`, resource requests (cpu: 100m, memory: 128Mi), labels `app: gitops-demo`, `app.kubernetes.io/part-of: demo`
- Service: ClusterIP on port 80 targeting container port 8080
- ConfigMap: `APP_LOG_LEVEL=info`, `APP_ENV=base`
- Base Kustomization must include deployment.yaml, service.yaml, and generate a ConfigMap via `configMapGenerator`

### Environment Overlays

- **Development**: namespace `gitops-demo-dev`, 1 replica, `APP_LOG_LEVEL=debug`, `APP_ENV=development`, resource requests (cpu: 50m, memory: 64Mi), limits (cpu: 200m, memory: 256Mi)
- **Staging**: namespace `gitops-demo-staging`, 2 replicas, `APP_LOG_LEVEL=info`, `APP_ENV=staging`, resource requests (cpu: 100m, memory: 128Mi), limits (cpu: 500m, memory: 512Mi)
- **Production**: namespace `gitops-demo-prod`, 3 replicas, `APP_LOG_LEVEL=warn`, `APP_ENV=production`, resource requests (cpu: 250m, memory: 256Mi), limits (cpu: 1000m, memory: 1Gi), plus a PodDisruptionBudget with `minAvailable: 2`

### Flux Resources

- `GitRepository`: URL `https://github.com/example/gitops-demo`, branch `main`, interval `1m`
- Three `Kustomization` resources (one per environment), each with:
  - `sourceRef` pointing to the GitRepository
  - `path` pointing to the corresponding overlay directory
  - `prune: true` and `force: false`
  - Health checks on the Deployment
  - Development: no dependencies, interval `5m`
  - Staging: `dependsOn` development Kustomization succeeding, interval `10m`
  - Production: `dependsOn` staging Kustomization succeeding, interval `15m`
- `ImageRepository`: scanning `ghcr.io/example/gitops-demo` every 5 minutes
- `ImagePolicy`: semver range `">=1.0.0 <2.0.0"` selecting the latest matching tag
- `ImageUpdateAutomation`: updates image tags in the `overlays/production/kustomization.yaml` via commit to the Git repo

### Expected Functionality

- Running `kustomize build overlays/development` produces a valid Deployment with 1 replica in the `gitops-demo-dev` namespace
- Running `kustomize build overlays/production` produces a Deployment with 3 replicas, a PDB with `minAvailable: 2`, and strict resource limits
- The Flux Kustomization for staging depends on development, and production depends on staging
- Image update automation targets only the production overlay

## Acceptance Criteria

- All YAML manifests are syntactically valid and parseable
- Base Kustomization builds correctly; all three overlays build and correctly override the base
- Each environment has the correct namespace, replica count, resource limits, and log level
- Production overlay includes a PodDisruptionBudget with `minAvailable: 2`
- Flux GitRepository, Kustomization, ImageRepository, ImagePolicy, and ImageUpdateAutomation resources are well-formed with correct API versions and spec fields
- Promotion dependencies enforce the order: development → staging → production
- Tests validate YAML structure, overlay correctness, and Flux resource references
