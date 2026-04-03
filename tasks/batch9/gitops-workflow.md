# Task: Implement a Multi-Environment GitOps Deployment Pipeline for Flux CD

## Background

Flux CD (https://github.com/fluxcd/flux2) is a GitOps toolkit for Kubernetes. A new Go package is needed that generates a complete multi-environment GitOps repository structure with Flux CD manifests, including Kustomization resources, HelmRelease resources, automated image update policies, and a promotion controller that handles staging-to-production promotion via pull request automation.

## Files to Create/Modify

- `cmd/flux-gitops-gen/main.go` (create) — CLI entry point that generates a complete GitOps repository structure from a YAML application specification
- `internal/generator/kustomization.go` (create) — Generates Flux `Kustomization` custom resources for each environment (dev, staging, production) with proper dependency ordering and health checks
- `internal/generator/helmrelease.go` (create) — Generates `HelmRelease` resources with environment-specific value overrides, interval configuration, and remediation policies
- `internal/generator/imageupdate.go` (create) — Generates `ImageRepository`, `ImagePolicy`, and `ImageUpdateAutomation` resources for automated container image updates
- `internal/generator/promotion.go` (create) — Implements a promotion controller that copies manifests from staging to production with approval gates, creates a patch set, and outputs a structured promotion plan
- `internal/generator/generator_test.go` (create) — Unit tests for all generators: valid YAML output, correct resource fields, environment isolation

## Requirements

### Application Specification (Input Format)

- Input YAML schema:
  ```yaml
  name: my-app
  team: platform
  environments:
    - name: dev
      namespace: dev
      auto_deploy: true
    - name: staging
      namespace: staging
      auto_deploy: true
    - name: production
      namespace: production
      auto_deploy: false
      requires_approval: true
  helm:
    chart: my-app
    repo: oci://registry.example.com/charts
    version: ">=1.0.0"
  images:
    - name: my-app
      image: registry.example.com/my-app
      policy: semver
      range: ">=1.0.0 <2.0.0"
  ```

### Kustomization Generator (`kustomization.go`)

- Function `GenerateKustomizations(spec AppSpec) ([]KustomizationManifest, error)`
- For each environment, generate a Flux `Kustomization` resource:
  - `apiVersion: kustomize.toolkit.fluxcd.io/v1`
  - `kind: Kustomization`
  - `spec.interval` — dev: `1m`, staging: `5m`, production: `10m`
  - `spec.path` — `./environments/<env-name>`
  - `spec.prune: true`
  - `spec.sourceRef` pointing to a `GitRepository` named `flux-system`
  - `spec.healthChecks` — list of deployment references to monitor
  - `spec.dependsOn` — production depends on staging Kustomization; staging depends on dev
- Production environment must include `spec.suspend: false` and must NOT set `spec.force: true`
- Each environment must set `spec.targetNamespace` to the environment's namespace

### HelmRelease Generator (`helmrelease.go`)

- Function `GenerateHelmReleases(spec AppSpec) ([]HelmReleaseManifest, error)`
- For each environment, generate a `HelmRelease` resource:
  - `apiVersion: helm.toolkit.fluxcd.io/v2beta2`
  - `kind: HelmRelease`
  - `spec.chart.spec.chart` from the spec's `helm.chart`
  - `spec.chart.spec.sourceRef` pointing to an `HelmRepository` or `OCIRepository`
  - `spec.chart.spec.version` — dev: latest semver, staging/production: pinned version from spec
  - `spec.values` — Environment-specific overrides (dev: `replicas: 1, debug: true`, staging: `replicas: 2`, production: `replicas: 3, resources.limits.memory: 512Mi`)
  - `spec.upgrade.remediation.retries: 3` for production
  - `spec.test.enable: true` for staging

### Image Update Generator (`imageupdate.go`)

- Function `GenerateImagePolicies(spec AppSpec) ([]Manifest, error)` — Returns three resources:
  1. `ImageRepository` — `spec.image` from config, `spec.interval: 1m0s`
  2. `ImagePolicy` — `spec.policy.semver.range` from config
  3. `ImageUpdateAutomation` — `spec.git.push.branch: main`, `spec.update.strategy: Setters`, `spec.interval: 1m0s`
- Only generate for environments with `auto_deploy: true`

### Promotion Controller (`promotion.go`)

- Function `GeneratePromotionPlan(staging, production KustomizationManifest) PromotionPlan`
- `PromotionPlan` struct: `Patches []FilePatch`, `RequiresApproval bool`, `Summary string`
- Compares staging and production manifests, produces patch set of field changes
- If production has `requires_approval: true`, set `RequiresApproval` flag
- Summary includes: number of changed resources, image version changes, value override diffs

### Directory Structure Output

Generated output must follow this structure:
```
output/
├── environments/
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   └── my-app-helmrelease.yaml
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   └── my-app-helmrelease.yaml
│   └── production/
│       ├── kustomization.yaml
│       └── my-app-helmrelease.yaml
├── image-policies/
│   ├── my-app-imagerepository.yaml
│   ├── my-app-imagepolicy.yaml
│   └── my-app-imageupdateautomation.yaml
└── flux-system/
    └── gotk-sync.yaml
```

### Expected Functionality

- Running the generator with a 3-environment app spec produces 9+ YAML files across the directory structure
- Production Kustomization depends on staging; staging depends on dev (dependency chain)
- HelmRelease for production uses 3 replicas and 512Mi memory limit; dev uses 1 replica with debug enabled
- Image update resources are only generated for environments with `auto_deploy: true`
- Promotion plan from staging to production shows the diff of helm values and image versions

## Acceptance Criteria

- All generated YAML files are valid and parseable by `yaml.Unmarshal`
- Kustomization resources have correct API version, intervals, and dependency ordering
- HelmRelease values differ correctly between environments
- Image update resources use the correct semver range from the spec
- Promotion controller correctly identifies differences between staging and production
- Directory structure matches the expected layout
- `python -m pytest /workspace/tests/test_gitops_workflow.py -v --tb=short` passes
