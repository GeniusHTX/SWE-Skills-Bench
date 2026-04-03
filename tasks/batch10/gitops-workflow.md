# Task: Implement GitOps Reconciliation Pipeline for Multi-Environment Flux CD Deployment

## Background

The Flux CD toolkit (`fluxcd/flux2`) manages Kubernetes deployments via Git-based reconciliation. The repository needs a new multi-environment deployment pipeline that provisions a staging and production environment from a single Git source, with automated sync policies, health-check gating, and dependency ordering between infrastructure components and application workloads. The implementation targets the `internal/` and `pkg/` packages where reconciliation logic is defined.

## Files to Create/Modify

- `internal/reconcile/pipeline.go` — New reconciliation pipeline that orchestrates multi-stage deployment across environments (new)
- `internal/reconcile/pipeline_test.go` — Unit tests for the reconciliation pipeline (new)
- `pkg/manifests/multi_env/` — Directory containing environment-specific Kustomization manifests (new)
- `pkg/manifests/multi_env/base/kustomization.yaml` — Base Kustomization with shared application resources (new)
- `pkg/manifests/multi_env/staging/kustomization.yaml` — Staging overlay with namespace and replica overrides (new)
- `pkg/manifests/multi_env/production/kustomization.yaml` — Production overlay with resource limits and HPA (new)
- `internal/reconcile/health.go` — Health gate evaluator that blocks promotion from staging to production (new)
- `internal/reconcile/health_test.go` — Unit tests for health gate evaluator (new)

## Requirements

### GitRepository Source Management

- Define a `GitRepositorySource` struct with fields: `URL string`, `Branch string`, `Interval time.Duration`, `SecretRef string`, `Suspend bool`
- Implement `Validate()` that rejects empty URL, intervals below 30 seconds, and branches containing `..` or whitespace
- Implement `Reconcile(ctx context.Context)` that returns a `SourceResult` with `Revision`, `Artifact` path, and `Ready` condition

### Kustomization Reconciliation

- Define a `KustomizationReconciler` struct managing an ordered list of `KustomizationSpec` entries
- Each `KustomizationSpec` contains: `Name`, `Path`, `SourceRef`, `Prune bool`, `HealthChecks []HealthCheck`, `DependsOn []string`, `Timeout time.Duration`, `Interval time.Duration`
- `Reconcile()` must process entries in dependency order — if spec A `DependsOn` spec B, B must reconcile successfully before A starts
- Circular dependencies must be detected and return a `CircularDependencyError` listing the cycle path
- When `Prune` is true, resources removed from the source must be tracked in a `PruneResult` listing deleted resource GVKs and names

### Environment Promotion Pipeline

- Define a `Pipeline` struct with `Stages []Stage` where each `Stage` has `Name`, `Environment string`, `Kustomizations []KustomizationSpec`, `Gates []GateFunc`
- `Pipeline.Execute(ctx context.Context)` processes stages sequentially; each stage's gate functions must all pass before advancing
- If a gate fails, the pipeline halts and returns a `GateFailedError` with stage name, gate index, and underlying message
- A `HealthGate` checks that all deployments in a namespace report `Available` condition `True` with `ObservedGeneration` matching `Generation`
- A `ManualApprovalGate` returns `ErrAwaitingApproval` until an approval token is set via `Pipeline.Approve(stageName string)`

### Kustomize Overlay Structure

- `base/kustomization.yaml` must declare: a `Deployment` named `web-app` with image `ghcr.io/org/web-app`, a `Service` named `web-app-svc` on port 8080, and a `ConfigMap` named `web-app-config`
- `staging/kustomization.yaml` patches namespace to `staging`, sets replicas to 1, adds label `env: staging`
- `production/kustomization.yaml` patches namespace to `production`, sets replicas to 3, adds resource limits (`cpu: 500m`, `memory: 512Mi`), adds label `env: production`

### Expected Functionality

- Creating a `GitRepositorySource` with URL `https://github.com/org/app`, branch `main`, interval `1m` → `Validate()` returns nil
- Creating a `GitRepositorySource` with empty URL → `Validate()` returns error containing "url is required"
- Creating a `GitRepositorySource` with interval `10s` → `Validate()` returns error containing "interval must be at least 30s"
- Reconciling kustomizations `[infra (no deps), app (depends on infra)]` → infra reconciles first, app second; returned order is `[infra, app]`
- Reconciling kustomizations `[A depends on B, B depends on A]` → returns `CircularDependencyError` mentioning both A and B
- Pipeline with stages `[staging, production]` where staging health gate passes → production stage executes
- Pipeline with stages `[staging, production]` where staging health gate fails → returns `GateFailedError` with stage "staging"
- Pipeline with `ManualApprovalGate` on production → returns `ErrAwaitingApproval`; after `Pipeline.Approve("production")`, re-execution proceeds past the gate
- Reconciling with `Prune: true` and a resource removed from source → `PruneResult` lists the removed resource

## Acceptance Criteria

- `go test ./internal/reconcile/ -v` passes all tests
- `GitRepositorySource.Validate()` rejects invalid URLs, short intervals, and malformed branch names
- Dependency-ordered reconciliation correctly sequences kustomizations and detects cycles
- `Pipeline.Execute()` halts at the first failing gate and reports the correct stage
- `ManualApprovalGate` blocks until explicit approval is granted
- Health gate evaluates deployment conditions with generation matching
- Kustomize overlays produce valid YAML that would be accepted by `kubectl apply --dry-run=client`
- Prune tracking correctly identifies resources removed between source revisions
- No hardcoded test values — all assertions validate structure and behavior
