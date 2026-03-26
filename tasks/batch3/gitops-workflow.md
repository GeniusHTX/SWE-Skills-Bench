# Task: Implement GitOps Application Deployment Configuration Generator for Flux

## Background

Flux (https://github.com/fluxcd/flux2) is a GitOps toolkit for continuous delivery on Kubernetes. The project needs a configuration generator that creates Flux custom resources for multi-environment application deployments, including source references, Kustomization resources, health checks, and progressive delivery configuration. This should integrate with Flux's existing API types in the `api/` directory.

## Files to Create/Modify

- `internal/gitops/app_generator.go` (create) — Application deployment configuration generator producing Flux CRDs
- `internal/gitops/environment.go` (create) — Multi-environment configuration with promotion and drift detection
- `internal/gitops/health_check.go` (create) — Health check and dependency configuration for Flux Kustomizations
- `internal/gitops/app_generator_test.go` (create) — Tests for application deployment configuration
- `internal/gitops/environment_test.go` (create) — Tests for environment management

## Requirements

### Application Configuration Generator

- Implement an `AppGenerator` struct that produces Flux `Kustomization` custom resources for deploying an application
- Input: application name, Git repository URL, branch, path within repo, target namespace, sync interval (default: `5m`)
- Output: a `Kustomization` YAML manifest with:
  - `apiVersion: kustomize.toolkit.fluxcd.io/v1` and `kind: Kustomization`
  - `sourceRef` pointing to a `GitRepository` resource
  - `path` set to the application's directory within the repo
  - `prune: true` (remove resources that are no longer in Git)
  - `targetNamespace` for the deployment
- Also generate the corresponding `GitRepository` resource with `apiVersion: source.toolkit.fluxcd.io/v1` and `kind: GitRepository`, including `url`, `ref.branch`, and `interval`

### Multi-Environment Promotion

- Implement an `EnvironmentManager` that generates configurations for `development`, `staging`, and `production` environments
- Each environment is a separate `Kustomization` pointing to a different path in the repo (e.g., `deploy/dev`, `deploy/staging`, `deploy/prod`)
- Environment-specific overrides:
  - `development`: `interval: 1m`, no approval required
  - `staging`: `interval: 5m`, depends on `development` Kustomization being healthy
  - `production`: `interval: 10m`, depends on `staging` Kustomization being healthy, uses `suspend: true` by default (manual approval needed to unsuspend)
- Implement a `promote(from_env, to_env)` method that generates the necessary config changes (unsuspend target, set dependency)
- `promote` to production without staging being healthy returns an error

### Health Checks

- Implement a `HealthCheckConfig` that adds health checks to Kustomization resources:
  - Deployment health: check that all replicas are available (via `Deployment` kind, apiVersion `apps/v1`)
  - Custom health check: check that a specific `Job` completes successfully (for database migrations)
  - Health check timeout: configurable, default `5m`
- Add `dependsOn` relationships between Kustomizations, ensuring the correct deployment order
- If a health check fails, the Kustomization should not proceed (Flux's built-in behavior); generate the config that enables this

### Drift Detection

- Generate a `Kustomization` field `force: true` to correct drift (force reapply if resources were manually modified)
- Add annotation `reconcile.fluxcd.io/requestedAt` with a timestamp to trigger immediate reconciliation when needed
- Provide a `detect_drift_config()` method that generates a Flux `Alert` resource to notify when drift is detected (type: `generic`, event: `Kustomization/*)

### Expected Functionality

- Generating config for app "web-frontend" with repo "https://github.com/org/app.git", branch "main", path "deploy/prod" produces correct Kustomization and GitRepository YAML
- Generating 3 environments produces 3 Kustomizations with correct paths and intervals
- The production Kustomization has `suspend: true` and depends on staging
- `promote("staging", "production")` generates config that unsuspends production and sets the dependency
- `promote("development", "production")` returns an error (must go through staging)
- A Kustomization with a Deployment health check includes the correct `healthChecks` entry

## Acceptance Criteria

- `AppGenerator` produces valid Flux `Kustomization` and `GitRepository` YAML with correct apiVersions and kinds
- Source references correctly point from Kustomization to GitRepository
- Multi-environment configuration generates correct paths, intervals, and dependencies per environment
- Production is suspended by default and depends on staging health
- `promote` validates environment ordering and produces correct configuration changes
- Health checks include Deployment and Job health check entries with configurable timeouts
- `dependsOn` relationships enforce correct deployment ordering
- Drift detection configuration generates correct Flux Alert resources
- Tests cover single-environment and multi-environment generation, promotion validation, health check configuration, and YAML correctness
